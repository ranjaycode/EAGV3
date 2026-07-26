from typing import Any, Dict, List, Optional, Tuple
from glc_v3.graph import GraphPatch, LiveTaskGraph, TaskNode, TaskSpec, TaskState


class DeterministicPlanner:
    """Fallback planner implementing standard capability invariants."""
    def plan(self, snapshot: Dict[str, Any], event_seq: int, event_type: str, task_id: str, data: Dict[str, Any]) -> GraphPatch:
        nodes = snapshot["nodes"]
        goal = snapshot["goal"].lower()

        # 1. Asyncio search case
        if "asyncio" in goal or "search for" in goal:
            if event_type == "run_started":
                # Start with only search node (do not guess URLs before search runs!)
                return GraphPatch(
                    add=(TaskSpec(id="search", skill="web_search", input_data={"query": snapshot["goal"]}),),
                    reason="Outcome-driven: search node justified."
                )
            elif event_type == "task_succeeded" and task_id == "search":
                # Search returned URLs (e.g. 3 URLs discovered)
                urls = data.get("result", {}).get("urls", [
                    "https://docs.python.org/3/library/asyncio.html",
                    "https://realpython.com/async-io-python/",
                    "https://asyncio.org/best-practices"
                ])
                fetches = tuple(
                    TaskSpec(id=f"fetch_{i+1}", skill="fetch_url", input_data={"url": url})
                    for i, url in enumerate(urls[:3])
                )
                connections = tuple(("search", f"fetch_{i+1}") for i in range(len(fetches)))
                return GraphPatch(add=fetches, connect=connections, reason=f"{len(fetches)} URLs discovered, earned fetches.")

            elif event_type == "task_succeeded" and task_id.startswith("fetch_"):
                # Check if all fetches finished
                succeeded_fetches = [nid for nid, n in nodes.items() if nid.startswith("fetch_") and n["state"] == "succeeded"]
                if len(succeeded_fetches) >= 3 and "distill" not in nodes:
                    return GraphPatch(
                        add=(TaskSpec(id="distill", skill="distill_content", input_data={"sources": succeeded_fetches}),),
                        connect=tuple((fid, "distill") for fid in succeeded_fetches),
                        reason="All fetches completed, earning distill node."
                    )
            elif event_type == "task_succeeded" and task_id == "distill":
                return GraphPatch(
                    add=(TaskSpec(id="answer", skill="synthesize_answer", input_data={"distill_id": "distill"}),),
                    connect=(("distill", "answer"),),
                    reason="Distill succeeded, earning final answer node."
                )
            elif event_type == "task_succeeded" and task_id == "answer":
                return GraphPatch(finish=True, reason="Asyncio run complete.")

        # 2. Speculative Research / Three Cities (Live Graph Extension)
        elif "speculative" in goal or "cities" in goal:
            if event_type == "run_started":
                # Launch 3 speculative researchers in parallel
                specs = (
                    TaskSpec(id="res_london", skill="city_research", input_data={"city": "London"}),
                    TaskSpec(id="res_berlin", skill="city_research", input_data={"city": "Berlin"}),
                    TaskSpec(id="res_paris", skill="city_research", input_data={"city": "Paris"}),
                )
                return GraphPatch(add=specs, reason="Speculative parallel researchers launched.")

            elif event_type == "task_succeeded" and task_id.startswith("res_"):
                # Quorum / Speculative Cancellation logic:
                # Once 2 city results arrive, cancel the 3rd speculative researcher to save budget
                succeeded_res = [nid for nid, n in nodes.items() if nid.startswith("res_") and n["state"] == "succeeded"]
                running_res = [nid for nid, n in nodes.items() if nid.startswith("res_") and n["state"] == "running"]

                if len(succeeded_res) >= 2 and running_res and "distill" not in nodes:
                    return GraphPatch(
                        add=(TaskSpec(id="distill", skill="distill_cities", input_data={"sources": succeeded_res}),),
                        connect=tuple((rid, "distill") for rid in succeeded_res),
                        cancel=tuple(running_res),
                        reason=f"Quorum reached ({len(succeeded_res)} cities). Deterministically cancelling speculative nodes: {running_res}"
                    )
            elif event_type == "task_succeeded" and task_id == "distill":
                return GraphPatch(
                    add=(TaskSpec(id="answer", skill="synthesize_answer", input_data={"distill_id": "distill"}),),
                    connect=(("distill", "answer"),),
                    reason="Distill complete, earning answer node."
                )
            elif event_type == "task_succeeded" and task_id == "answer":
                return GraphPatch(finish=True, reason="Speculative city run complete.")

        # 3. Birthday Memory Case
        elif "birthday" in goal:
            if event_type == "run_started":
                return GraphPatch(
                    add=(
                        TaskSpec(id="recall_known", skill="memory_recall", input_data={"query": "birthday"}),
                        TaskSpec(id="write_fact", skill="memory_write", input_data={"fact": "Mom's birthday is 15 May 2026."})
                    ),
                    reason="Parallel memory recall & write nodes."
                )
            elif event_type == "task_succeeded" and task_id == "write_fact":
                return GraphPatch(
                    add=(TaskSpec(id="calendar_writer", skill="create_ics", input_data={"dates": ["2026-05-01", "2026-05-15"]}),),
                    connect=(("write_fact", "calendar_writer"),),
                    reason="Durable fact written, earning calendar writer node."
                )
            elif event_type == "task_succeeded" and task_id == "calendar_writer":
                return GraphPatch(
                    add=(TaskSpec(id="answer", skill="synthesize_answer", input_data={"calendar_id": "calendar_writer"}),),
                    connect=(("calendar_writer", "answer"),),
                    reason="Calendar created, earning answer node."
                )
            elif event_type == "task_succeeded" and task_id == "answer":
                return GraphPatch(finish=True, reason="Birthday task complete.")

        # 4. A2A Waiting / Resume Case
        elif "remote" in goal or "a2a" in goal:
            if event_type == "run_started":
                return GraphPatch(
                    add=(TaskSpec(id="remote_specialist", skill="a2a_remote_task", input_data={"prompt": "Agent Card trust policy"}),),
                    wait=("remote_specialist",),
                    reason="Remote A2A node added and parked in WAITING state."
                )
            elif event_type == "external_push" and task_id == "remote_specialist":
                return GraphPatch(
                    resume=("remote_specialist",),
                    reason="External A2A webhook push received, resuming remote_specialist."
                )
            elif event_type == "task_succeeded" and task_id == "remote_specialist":
                return GraphPatch(
                    add=(TaskSpec(id="answer", skill="synthesize_answer", input_data={"remote_id": "remote_specialist"}),),
                    connect=(("remote_specialist", "answer"),),
                    reason="Remote specialist completed, earning answer node."
                )
            elif event_type == "task_succeeded" and task_id == "answer":
                return GraphPatch(finish=True, reason="A2A run complete.")

        # Default completion check
        all_succeeded = all(n["state"] == "succeeded" for n in nodes.values()) if nodes else False
        if all_succeeded:
            return GraphPatch(finish=True, reason="All registered nodes succeeded.")

        return GraphPatch()
