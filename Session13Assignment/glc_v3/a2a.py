import hashlib
import hmac
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class A2ATaskStatus(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentCard:
    name: str
    description: str
    version: str
    supportedInterfaces: List[Dict[str, str]]
    capabilities: Dict[str, bool]
    skills: List[Dict[str, Any]]
    signature: Optional[str] = None

    def validate_schema(self) -> bool:
        if not self.name or not self.version or not self.supportedInterfaces:
            return False
        return True


@dataclass
class A2AMessage:
    role: str
    content: str
    media_type: str = "text/plain"


@dataclass
class A2AArtifact:
    artifact_id: str
    name: str
    media_type: str
    content: Any


@dataclass
class A2ATask:
    task_id: str
    context_id: str
    status: A2ATaskStatus
    input_message: A2AMessage
    output_artifact: Optional[A2AArtifact] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class A2AServiceHandler:
    """Agent2Agent 1.0 Protocol Service Handler & Isolation Gateway."""
    def __init__(self, agent_card: AgentCard):
        self.agent_card = agent_card
        self.tasks: Dict[str, A2ATask] = {}
        self.idempotency_ledger: Set[str] = set()

    def get_agent_card(self) -> Dict[str, Any]:
        return asdict(self.agent_card)

    def send_message_sync(self, context_id: str, message: A2AMessage, secret_key: str = "default_secret") -> A2ATask:
        task_id = f"a2a_task_{uuid.uuid4().hex[:8]}"
        task = A2ATask(
            task_id=task_id,
            context_id=context_id,
            status=A2ATaskStatus.WORKING,
            input_message=message
        )
        self.tasks[task_id] = task

        # Simulate remote autonomous agent execution (without granting local memory handles)
        response_text = f"A2A Sourced Synthesis: Processed '{message.content[:50]}...'"
        artifact = A2AArtifact(
            artifact_id=f"art_{uuid.uuid4().hex[:6]}",
            name="synthesis_report",
            media_type="text/plain",
            content=response_text
        )

        task.status = A2ATaskStatus.COMPLETED
        task.output_artifact = artifact
        task.updated_at = time.time()
        return task

    def receive_async_push(
        self,
        payload: Dict[str, Any],
        signature: str,
        idempotency_key: str,
        secret: str = "a2a_shared_secret"
    ) -> Dict[str, Any]:
        # Step 1: Idempotency deduplication check
        if idempotency_key in self.idempotency_ledger:
            return {"status": "duplicate_suppressed", "idempotency_key": idempotency_key}

        # Step 2: HMAC-SHA256 Signature Verification
        computed_sig = hmac.new(
            secret.encode("utf-8"),
            json.dumps(payload, sort_keys=True).encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, computed_sig):
            raise PermissionError("A2A Push Signature Verification Failed: Tampered or invalid signature.")

        # Record idempotency
        self.idempotency_ledger.add(idempotency_key)

        task_id = payload.get("task_id", "")
        status_str = payload.get("status", "completed")

        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = A2ATaskStatus(status_str)
            task.updated_at = time.time()
            if "artifact" in payload:
                task.output_artifact = A2AArtifact(**payload["artifact"])

        return {"status": "accepted", "task_id": task_id}
