import json
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False


class MemoryKind(str, Enum):
    WORKING = "working"
    EPISODE = "episode"
    FACT = "fact"
    PLAYBOOK = "playbook"
    POLICY = "policy"
    AUDIT = "audit"
    DOCUMENT_CHUNK = "document_chunk"


@dataclass
class MemoryScope:
    tenant_id: str
    project_id: str
    user_id: str
    agent_id: str
    run_id: Optional[str] = None

    def matches(self, other: "MemoryScope") -> bool:
        return (
            self.tenant_id == other.tenant_id
            and self.project_id == other.project_id
            and self.user_id == other.user_id
            and self.agent_id == other.agent_id
        )


@dataclass
class SourceRef:
    uri: str
    author: str


@dataclass
class Principal:
    id: str
    role: str  # "agent", "system", "operator", "user"


@dataclass
class MemoryRecord:
    id: str
    kind: MemoryKind
    scope: MemoryScope
    text: str
    sources: List[SourceRef]
    principal: Principal
    confidence: float = 1.0
    status: str = "current"  # "current" | "superseded"
    supersedes_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EvidenceCard:
    """Attributed memory evidence card for downstream model reasoning."""
    def __init__(
        self,
        record_id: str,
        kind: MemoryKind,
        text: str,
        source_uri: str,
        score: float,
        scope: MemoryScope,
        attribution: str = "stated"  # "stated" | "derived" | "inferred"
    ):
        self.record_id = record_id
        self.kind = kind
        self.text = text
        self.source_uri = source_uri
        self.score = score
        self.scope = scope
        self.attribution = attribution

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "kind": self.kind.value,
            "text": self.text,
            "source_uri": self.source_uri,
            "score": self.score,
            "scope": asdict(self.scope),
            "attribution": self.attribution
        }


class MemoryService:
    """7-Drawer Typed Memory Service using SQLite as Source of Truth and FAISS for ANN Search."""
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

        # FAISS setup (384-dimensional space)
        self.dimension = 384
        if HAS_FAISS:
            self.faiss_index = faiss.IndexFlatL2(self.dimension)
        else:
            self.faiss_index = None
        self.faiss_id_map: List[str] = []

    def _init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_records (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    run_id TEXT,
                    text TEXT NOT NULL,
                    sources TEXT NOT NULL,
                    principal_id TEXT NOT NULL,
                    principal_role TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    status TEXT NOT NULL,
                    supersedes_id TEXT,
                    created_at REAL NOT NULL,
                    metadata TEXT NOT NULL
                )
            """)

    def _mock_embedding(self, text: str) -> np.ndarray:
        """Generates a deterministic 384-dim vector for fast search/testing."""
        np.random.seed(abs(hash(text)) % (2**32))
        vec = np.random.randn(self.dimension).astype("float32")
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def write_record(self, record: MemoryRecord) -> str:
        # Authority check
        if record.kind == MemoryKind.POLICY and record.principal.role not in ("operator", "system"):
            raise PermissionError("Only operator or system principals may write POLICY memory.")
        if record.kind == MemoryKind.AUDIT and record.principal.role != "system":
            raise PermissionError("AUDIT drawer is append-only for system principals.")

        # Supersession handling
        if record.supersedes_id:
            with self.conn:
                self.conn.execute(
                    "UPDATE memory_records SET status = 'superseded' WHERE id = ?",
                    (record.supersedes_id,)
                )

        # Write to SQLite
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO memory_records (
                    id, kind, tenant_id, project_id, user_id, agent_id, run_id,
                    text, sources, principal_id, principal_role, confidence,
                    status, supersedes_id, created_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.kind.value,
                    record.scope.tenant_id,
                    record.scope.project_id,
                    record.scope.user_id,
                    record.scope.agent_id,
                    record.scope.run_id,
                    record.text,
                    json.dumps([asdict(s) for s in record.sources]),
                    record.principal.id,
                    record.principal.role,
                    record.confidence,
                    record.status,
                    record.supersedes_id,
                    record.created_at,
                    json.dumps(record.metadata)
                )
            )

        # Add to FAISS index
        vec = self._mock_embedding(record.text)
        if HAS_FAISS and self.faiss_index is not None:
            self.faiss_index.add(np.array([vec]))
            self.faiss_id_map.append(record.id)

        return record.id

    def recall(
        self,
        query: str,
        scope: MemoryScope,
        kinds: Optional[List[MemoryKind]] = None,
        top_k: int = 5
    ) -> List[EvidenceCard]:
        # Scope-first filtering
        kind_clause = ""
        params: List[Any] = [scope.tenant_id, scope.project_id, scope.user_id, scope.agent_id]

        if kinds:
            placeholders = ",".join("?" for _ in kinds)
            kind_clause = f" AND kind IN ({placeholders})"
            params.extend([k.value for k in kinds])

        cursor = self.conn.execute(
            f"""
            SELECT id, kind, text, sources, status FROM memory_records
            WHERE tenant_id = ? AND project_id = ? AND user_id = ? AND agent_id = ?
            AND status = 'current' {kind_clause}
            """,
            params
        )
        rows = cursor.fetchall()
        if not rows:
            return []

        # Vector search scoring over candidates
        query_vec = self._mock_embedding(query)
        evidence_cards = []

        for row in rows:
            rec_id, kind_str, text, sources_json, status = row
            rec_vec = self._mock_embedding(text)
            sim_score = float(np.dot(query_vec, rec_vec))

            sources = json.loads(sources_json)
            source_uri = sources[0]["uri"] if sources else "api://agent/runs"

            card = EvidenceCard(
                record_id=rec_id,
                kind=MemoryKind(kind_str),
                text=text,
                source_uri=source_uri,
                score=sim_score,
                scope=scope,
                attribution="stated"
            )
            evidence_cards.append(card)

        evidence_cards.sort(key=lambda c: c.score, reverse=True)
        return evidence_cards[:top_k]

    def get_record(self, record_id: str) -> Optional[MemoryRecord]:
        cursor = self.conn.execute(
            "SELECT id, kind, tenant_id, project_id, user_id, agent_id, run_id, text, sources, principal_id, principal_role, confidence, status, supersedes_id, created_at, metadata FROM memory_records WHERE id = ?",
            (record_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        (
            rec_id, kind_str, tenant_id, project_id, user_id, agent_id, run_id,
            text, sources_json, principal_id, principal_role, confidence,
            status, supersedes_id, created_at, metadata_json
        ) = row

        sources = [SourceRef(**s) for s in json.loads(sources_json)]
        principal = Principal(id=principal_id, role=principal_role)
        scope = MemoryScope(tenant_id=tenant_id, project_id=project_id, user_id=user_id, agent_id=agent_id, run_id=run_id)

        return MemoryRecord(
            id=rec_id,
            kind=MemoryKind(kind_str),
            scope=scope,
            text=text,
            sources=sources,
            principal=principal,
            confidence=confidence,
            status=status,
            supersedes_id=supersedes_id,
            created_at=created_at,
            metadata=json.loads(metadata_json)
        )
