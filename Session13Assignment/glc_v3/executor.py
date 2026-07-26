import asyncio
import time
from typing import Any, Dict, Optional, Set
from glc_v3.graph import GraphPatch, LiveTaskGraph, TaskNode, TaskState
from glc_v3.planners import DeterministicPlanner
from glc_v3.providers import ProviderRouter


class TaskSkillRunner:
    """Simulates/Executes skill logic assigned to graph task nodes."""
    def __init__(self, provider_router: ProviderRouter):
        self.router = provider_router

    async def run_skill(self, node: TaskNode) -> Dict[str, Any]:
        slot = self.router.acquire_slot(node.spec.skill)
        skill = node.spec.skill
        inp = node.spec.input_data

        # Simulate execution work
        await asyncio.sleep(0.05)

        if skill == "web_search":
            return {
                "urls": [
                    "https://docs.python.org/3/library/asyncio.html",
                    "https://realpython.com/async-io-python/",
                    "https://asyncio.org/best-practices"
                ],
                "provider_slot": slot.name
            }
        elif skill == "fetch_url":
            return {
                "url": inp.get("url"),
                "content": f"Content snippet from {inp.get('url')}: asyncio best practices...",
                "provider_slot": slot.name
            }
        elif skill == "distill_content":
            return {
                "practices": [
                    "use asyncio for I/O-bound work",
                    "never block the event loop",
                    "actually await or schedule coroutines",
                    "use async context managers",
                    "bound concurrency",
                    "handle task exceptions"
                ],
                "provider_slot": slot.name
            }
        elif skill == "city_research":
            city = inp.get("city", "City")
            pop_map = {"London": "9.5M", "Berlin": "3.7M", "Paris": "2.1M"}
            return {"city": city, "population": pop_map.get(city, "1.0M"), "provider_slot": slot.name}
        elif skill == "distill_cities":
            return {"closest_pair": ["Berlin", "Paris"], "difference": "1.64M", "provider_slot": slot.name}
        elif skill == "memory_recall":
            return {"found": True, "fact": "Mom's birthday is 15 May 2026.", "provider_slot": slot.name}
        elif skill == "memory_write":
            return {"status": "written", "record_id": "mem_birthday_001", "provider_slot": slot.name}
        elif skill == "create_ics":
            return {"artifacts": ["reminder_may01.ics", "reminder_may15.ics"], "provider_slot": slot.name}
        elif skill == "a2a_remote_task":
            return {
                "artifact": "An Agent Card advertises capabilities; it grants no local-memory authority.",
                "provider_slot": slot.name
            }
        elif skill == "synthesize_answer":
            return {
                "answer": "Completed synthesis based on justified graph evidence.",
                "provider_slot": slot.name
            }
        else:
            return {"result": f"Executed {skill}", "provider_slot": slot.name}


class LiveExecutor:
    """Executes live task graph using asyncio.FIRST_COMPLETED loop."""
    def __init__(self, graph: LiveTaskGraph, max_workers: int = 3, provider_router: Optional[ProviderRouter] = None):
        self.graph = graph
        self.max_workers = max_workers
        self.router = provider_router or ProviderRouter()
        self.runner = TaskSkillRunner(self.router)
        self.planner = DeterministicPlanner()

        self.in_flight: Dict[str, asyncio.Task] = {}

    async def run(self) -> Dict[str, Any]:
        # Initial planning step
        snap = self.graph.snapshot()
        patch = self.planner.plan(snap, 1, "run_started", "", {})
        self.graph.apply_patch(patch, trigger_sequence=1)

        while not self.graph.finished:
            # Launch ready nodes up to max_workers
            ready_nodes = self.graph.get_ready_nodes()
            for node in ready_nodes:
                if len(self.in_flight) >= self.max_workers:
                    break
                tid = node.spec.id
                if tid not in self.in_flight:
                    self.graph.set_state(tid, TaskState.RUNNING)
                    task = asyncio.create_task(self.runner.run_skill(node))
                    self.in_flight[tid] = task

            if not self.in_flight:
                # Check if waiting nodes exist
                waiting_nodes = [n for n in self.graph.nodes.values() if n.state == TaskState.WAITING]
                if waiting_nodes:
                    # Parked waiting for external push/event
                    break
                else:
                    # No tasks running and no tasks ready -> finish
                    break

            # Wait for FIRST_COMPLETED
            done, pending = await asyncio.wait(
                self.in_flight.values(),
                return_when=asyncio.FIRST_COMPLETED
            )

            for completed_task in done:
                # Find task ID
                tid = None
                for t_id, task in list(self.in_flight.items()):
                    if task == completed_task:
                        tid = t_id
                        del self.in_flight[t_id]
                        break

                if not tid:
                    continue

                try:
                    res = completed_task.result()
                    # Record outcome event
                    self.graph.set_state(tid, TaskState.SUCCEEDED, result=res)
                    evt = self.graph.journal.events[-1]

                    # Plan next graph patch
                    snap = self.graph.snapshot()
                    patch = self.planner.plan(snap, evt.sequence, "task_succeeded", tid, {"result": res})
                    self.graph.apply_patch(patch, trigger_sequence=evt.sequence)

                    # Handle cancellation of in-flight tasks by patch
                    for cancel_id in patch.cancel:
                        if cancel_id in self.in_flight:
                            self.in_flight[cancel_id].cancel()
                            del self.in_flight[cancel_id]

                except Exception as ex:
                    self.graph.set_state(tid, TaskState.FAILED, error=str(ex))
                    evt = self.graph.journal.events[-1]
                    snap = self.graph.snapshot()
                    patch = self.planner.plan(snap, evt.sequence, "task_failed", tid, {"error": str(ex)})
                    self.graph.apply_patch(patch, trigger_sequence=evt.sequence)

        return self.graph.snapshot()

    def handle_external_event(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handles external push/webhook arrival to resume parked WAITING nodes."""
        if task_id in self.graph.nodes:
            evt = self.graph.journal.record("external_push", task_id=task_id, data=payload)
            snap = self.graph.snapshot()
            patch = self.planner.plan(snap, evt.sequence, "external_push", task_id, payload)
            self.graph.apply_patch(patch, trigger_sequence=evt.sequence)

            # Set node to succeeded with external result
            self.graph.set_state(task_id, TaskState.SUCCEEDED, result=payload)
        return self.graph.snapshot()
