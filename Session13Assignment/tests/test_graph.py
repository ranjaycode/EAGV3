import pytest
import asyncio
from glc_v3.graph import LiveTaskGraph, GraphPatch, TaskSpec, TaskState
from glc_v3.executor import LiveExecutor
from glc_v3.providers import ProviderRouter


@pytest.mark.asyncio
async def test_live_graph_expansion():
    graph = LiveTaskGraph(run_id="test_run_1", goal="Search for 'Python asyncio best practices'")
    executor = LiveExecutor(graph, max_workers=3)

    snapshot = await executor.run()
    assert snapshot["finished"] is True
    assert "search" in snapshot["nodes"]
    assert "fetch_1" in snapshot["nodes"]
    assert "distill" in snapshot["nodes"]
    assert "answer" in snapshot["nodes"]
    assert snapshot["nodes"]["answer"]["state"] == "succeeded"


def test_idempotent_patch_application():
    graph = LiveTaskGraph(run_id="test_run_2", goal="Test idempotency")
    patch = GraphPatch(add=(TaskSpec(id="t1", skill="test"),), reason="First add")

    applied_first = graph.apply_patch(patch, trigger_sequence=10)
    assert applied_first is True
    assert "t1" in graph.nodes

    # Re-applying same trigger sequence must return False and not duplicate
    applied_second = graph.apply_patch(patch, trigger_sequence=10)
    assert applied_second is False
    assert len(graph.nodes) == 1
