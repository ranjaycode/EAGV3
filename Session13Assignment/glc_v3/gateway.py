import uuid
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel

from glc_v3.a2a import A2AMessage, A2ATaskStatus, A2AServiceHandler, AgentCard
from glc_v3.chunking import Phi4SemanticSegmenter, SemanticIndexer
from glc_v3.executor import LiveExecutor
from glc_v3.graph import LiveTaskGraph
from glc_v3.memory import MemoryKind, MemoryRecord, MemoryScope, MemoryService, Principal, SourceRef
from glc_v3.providers import ProviderRouter

app = FastAPI(title="glc_v3 Gateway", version="3.0.0")

# Services setup
provider_router = ProviderRouter()
memory_service = MemoryService()
indexer = SemanticIndexer(memory_service)

agent_card = AgentCard(
    name="glc_v3 Autonomous Gateway Agent",
    description="Session 13 Live Task Graph, 7-Drawer Memory, Rohan V2 Chunking & A2A 1.0 Gateway",
    version="3.0.0",
    supportedInterfaces=[
        {"url": "http://127.0.0.1:8111/v1/a2a", "protocolBinding": "JSONRPC", "protocolVersion": "1.0"},
        {"url": "dns:///127.0.0.1:50051", "protocolBinding": "GRPC", "protocolVersion": "1.0"}
    ],
    capabilities={"streaming": True, "pushNotifications": True},
    skills=[
        {"id": "research", "name": "Technical Research", "description": "Dynamic evidence-driven synthesis"}
    ]
)
a2a_handler = A2AServiceHandler(agent_card)

# In-memory store for active runs
active_runs: Dict[str, LiveExecutor] = {}


class RunRequest(BaseModel):
    prompt: str
    tenant_id: str = "course"
    project_id: str = "s13"
    user_id: str = "student-01"
    agent_id: str = "assistant"
    max_workers: int = 3


class DocumentIndexRequest(BaseModel):
    text: str
    source_uri: str
    source_author: str = "student-01"
    tenant_id: str = "course"
    project_id: str = "s13"
    user_id: str = "student-01"
    agent_id: str = "assistant"


@app.get("/healthz")
def healthz():
    return {
        "status": "healthy",
        "version": "3.0.0",
        "providers": provider_router.get_slot_status()
    }


@app.get("/.well-known/agent-card.json")
def get_agent_card():
    return a2a_handler.get_agent_card()


@app.post("/v1/agent/runs")
async def create_run(req: RunRequest):
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    graph = LiveTaskGraph(run_id=run_id, goal=req.prompt)
    executor = LiveExecutor(graph=graph, max_workers=req.max_workers, provider_router=provider_router)
    active_runs[run_id] = executor

    snapshot = await executor.run()
    return {
        "run_id": run_id,
        "snapshot": snapshot,
        "events": [
            {
                "sequence": e.sequence,
                "event_type": e.event_type,
                "task_id": e.task_id,
                "data": e.data
            }
            for e in graph.journal.events
        ]
    }


@app.get("/v1/agent/runs/{run_id}")
def get_run(run_id: str):
    if run_id not in active_runs:
        raise HTTPException(status_code=404, detail="Run not found")
    executor = active_runs[run_id]
    graph = executor.graph
    return {
        "run_id": run_id,
        "snapshot": graph.snapshot(),
        "events": [
            {
                "sequence": e.sequence,
                "event_type": e.event_type,
                "task_id": e.task_id,
                "data": e.data
            }
            for e in graph.journal.events
        ]
    }


@app.post("/v1/agent/documents")
def index_document(req: DocumentIndexRequest):
    scope = MemoryScope(
        tenant_id=req.tenant_id,
        project_id=req.project_id,
        user_id=req.user_id,
        agent_id=req.agent_id
    )
    principal = Principal(id=req.agent_id, role="agent")

    res = indexer.index_document(
        text=req.text,
        source_uri=req.source_uri,
        author=req.source_author,
        scope=scope,
        principal=principal
    )
    return res


@app.post("/v1/a2a/push")
def a2a_push_receiver(
    payload: Dict[str, Any],
    x_a2a_signature: str = Header(...),
    x_idempotency_key: str = Header(...)
):
    try:
        res = a2a_handler.receive_async_push(
            payload=payload,
            signature=x_a2a_signature,
            idempotency_key=x_idempotency_key
        )
        return res
    except PermissionError as ex:
        raise HTTPException(status_code=401, detail=str(ex))
