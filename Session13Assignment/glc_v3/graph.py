import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"


@dataclass
class TaskSpec:
    id: str
    skill: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    provider: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphPatch:
    add: Tuple[TaskSpec, ...] = ()
    connect: Tuple[Tuple[str, str], ...] = ()  # (parent_id, child_id)
    cancel: Tuple[str, ...] = ()
    wait: Tuple[str, ...] = ()
    resume: Tuple[str, ...] = ()
    finish: bool = False
    reason: str = ""


@dataclass
class TaskNode:
    spec: TaskSpec
    state: TaskState = TaskState.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class Event:
    sequence: int
    event_type: str
    task_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class EventJournal:
    """Idempotent durable event log for run execution history."""
    def __init__(self):
        self.events: List[Event] = []
        self._next_seq: int = 1
        self._applied_sequences: Set[int] = set()

    def record(self, event_type: str, task_id: str = "", data: Optional[Dict[str, Any]] = None) -> Event:
        evt = Event(
            sequence=self._next_seq,
            event_type=event_type,
            task_id=task_id,
            data=data or {},
            timestamp=time.time()
        )
        self._next_seq += 1
        self.events.append(evt)
        return evt

    def is_patch_applied_for_sequence(self, sequence: int) -> bool:
        return sequence in self._applied_sequences

    def mark_patch_applied(self, sequence: int):
        self._applied_sequences.add(sequence)


class LiveTaskGraph:
    """Live Task Graph data structure maintaining nodes, edges, states, and patch operations."""
    def __init__(self, run_id: str, goal: str):
        self.run_id = run_id
        self.goal = goal
        self.nodes: Dict[str, TaskNode] = {}
        # edges: child_id -> set of parent_ids it depends on
        self.dependencies: Dict[str, Set[str]] = {}
        # reverse edges: parent_id -> set of child_ids depending on it
        self.dependents: Dict[str, Set[str]] = {}
        self.finished: bool = False
        self.journal = EventJournal()

        # Record run startup event
        self.journal.record("run_started", data={"goal": goal, "run_id": run_id})

    def add_node(self, spec: TaskSpec) -> TaskNode:
        if spec.id in self.nodes:
            return self.nodes[spec.id]
        node = TaskNode(spec=spec)
        self.nodes[spec.id] = node
        self.dependencies[spec.id] = set()
        self.dependents[spec.id] = set()
        return node

    def connect(self, parent_id: str, child_id: str):
        if parent_id in self.nodes and child_id in self.nodes:
            self.dependencies[child_id].add(parent_id)
            self.dependents[parent_id].add(child_id)

    def set_state(self, task_id: str, state: TaskState, result: Any = None, error: Optional[str] = None):
        if task_id not in self.nodes:
            return
        node = self.nodes[task_id]
        node.state = state
        node.updated_at = time.time()
        if result is not None:
            node.result = result
        if error is not None:
            node.error = error

        self.journal.record(f"task_{state.value}", task_id=task_id, data={"result": result, "error": error})

    def is_ready(self, task_id: str) -> bool:
        if task_id not in self.nodes:
            return False
        node = self.nodes[task_id]
        if node.state != TaskState.PENDING:
            return False
        # All parent dependencies must be SUCCEEDED
        parents = self.dependencies.get(task_id, set())
        for parent_id in parents:
            parent_node = self.nodes.get(parent_id)
            if not parent_node or parent_node.state != TaskState.SUCCEEDED:
                return False
        return True

    def get_ready_nodes(self) -> List[TaskNode]:
        """(Instance method) Returns nodes in PENDING state whose dependencies are satisfied."""
        return [node for node in self.nodes.values() if self.is_ready(node.spec.id)]

    def apply_patch(self, patch: GraphPatch, trigger_sequence: Optional[int] = None) -> bool:
        """Applies a GraphPatch idempotently."""
        if trigger_sequence is not None and self.journal.is_patch_applied_for_sequence(trigger_sequence):
            return False  # Already applied, idempotent skip

        # 1. Add new task nodes
        added_ids = []
        for spec in patch.add:
            self.add_node(spec)
            added_ids.append(spec.id)

        # 2. Connect dependencies
        for parent_id, child_id in patch.connect:
            self.connect(parent_id, child_id)

        # 3. Cancel nodes
        for cancel_id in patch.cancel:
            if cancel_id in self.nodes:
                node = self.nodes[cancel_id]
                if node.state in (TaskState.PENDING, TaskState.RUNNING, TaskState.WAITING):
                    self.set_state(cancel_id, TaskState.CANCELLED)

        # 4. Wait nodes (park for external event)
        for wait_id in patch.wait:
            if wait_id in self.nodes:
                node = self.nodes[wait_id]
                if node.state in (TaskState.PENDING, TaskState.RUNNING):
                    self.set_state(wait_id, TaskState.WAITING)

        # 5. Resume nodes
        for resume_id in patch.resume:
            if resume_id in self.nodes:
                node = self.nodes[resume_id]
                if node.state == TaskState.WAITING:
                    self.set_state(resume_id, TaskState.PENDING)

        # 6. Finish flag
        if patch.finish:
            self.finished = True
            self.journal.record("run_finished", data={"reason": patch.reason})

        if trigger_sequence is not None:
            self.journal.mark_patch_applied(trigger_sequence)

        self.journal.record("graph_patched", data={
            "added": added_ids,
            "connected": list(patch.connect),
            "cancelled": list(patch.cancel),
            "waited": list(patch.wait),
            "resumed": list(patch.resume),
            "finish": patch.finish,
            "reason": patch.reason
        })
        return True

    def snapshot(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "goal": self.goal,
            "finished": self.finished,
            "nodes": {
                tid: {
                    "id": node.spec.id,
                    "skill": node.spec.skill,
                    "input_data": node.spec.input_data,
                    "provider": node.spec.provider,
                    "state": node.state.value,
                    "result": node.result,
                    "error": node.error
                }
                for tid, node in self.nodes.items()
            },
            "dependencies": {tid: list(parents) for tid, parents in self.dependencies.items()},
            "event_count": len(self.journal.events)
        }
