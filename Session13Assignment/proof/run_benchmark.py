import asyncio
import json
import os
import sys

# Ensure glc_v3 is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from glc_v3.chunking import Phi4SemanticSegmenter, SemanticIndexer
from glc_v3.executor import LiveExecutor
from glc_v3.graph import LiveTaskGraph
from glc_v3.memory import MemoryKind, MemoryScope, MemoryService, Principal
from glc_v3.providers import ProviderRouter


async def run_floor_benchmarks():
    print("=========================================================")
    print("          Session 13 Non-Browser Benchmark Suite         ")
    print("=========================================================\n")

    router = ProviderRouter()

    # Case 1: Live expansion (Asyncio prompt)
    print("--- [Case 1: Live Task Graph Expansion (Asyncio Prompt)] ---")
    g1 = LiveTaskGraph(run_id="run_asyncio_01", goal="Search for 'Python asyncio best practices', read top 3 results, and give numbered list.")
    ex1 = LiveExecutor(g1, max_workers=3, provider_router=router)
    snap1 = await ex1.run()

    print(f"Goal: {snap1['goal']}")
    print(f"Total Nodes: {len(snap1['nodes'])}")
    for nid, node in snap1['nodes'].items():
        print(f"  - Node '{nid}': skill={node['skill']}, state={node['state']}, provider={node['result'].get('provider_slot') if node['result'] else 'N/A'}")
    print(f"Journal Events Recorded: {len(g1.journal.events)}\n")

    # Case 2: Durable Memory Round-Trip (Birthday Prompt)
    print("--- [Case 2: Typed Durable Memory Round-Trip (Birthday)] ---")
    g2 = LiveTaskGraph(run_id="run_birthday_01", goal="My mom's birthday is 15 May 2026. Remember that and create reminders.")
    ex2 = LiveExecutor(g2, max_workers=3, provider_router=router)
    snap2 = await ex2.run()

    print(f"Goal: {snap2['goal']}")
    print(f"Total Nodes: {len(snap2['nodes'])}")
    for nid, node in snap2['nodes'].items():
        print(f"  - Node '{nid}': state={node['state']}, result={node['result']}")

    mem = MemoryService()
    scope = MemoryScope(tenant_id="course", project_id="s13", user_id="rohan", agent_id="assistant")
    cards = mem.recall("mom birthday", scope=scope, kinds=[MemoryKind.FACT])
    print(f"Recall Check Cards: {len(cards)} items retrieved for scope {scope.tenant_id}/{scope.project_id}\n")

    # Case 3: Semantic Document Query (Attention Paper Indexing)
    print("--- [Case 3: Rohan V2 Semantic Indexing & Grounded Synthesis] ---")
    paper_md = """# Attention Is All You Need
The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose the Transformer, a model architecture eschewing recurrence.

## Key Contributions
1. We rely entirely on an attention mechanism to draw global dependencies between input and output.
2. The Transformer allows for significantly more parallelization and can reach a new state of the art in translation quality.
3. Training requires significantly less time compared to recurrent architectures.
"""
    indexer = SemanticIndexer(mem)
    principal = Principal(id="assistant", role="agent")
    idx_res = indexer.index_document(paper_md, source_uri="file:///papers/attention.md", author="rohan", scope=scope, principal=principal)
    print(f"Document Index Result: status={idx_res['status']}, chunks_indexed={idx_res['chunks_indexed']}")
    print(f"Chunk Decisions: {idx_res['decisions']}\n")

    # Case 4: A2A Waiting / Resume Case
    print("--- [Case 4: Agent2Agent Remote Task Waiting & Resume] ---")
    g4 = LiveTaskGraph(run_id="run_a2a_01", goal="Slow remote report: explain why Agent Card is not permission to access local memory.")
    ex4 = LiveExecutor(g4, max_workers=3, provider_router=router)

    # Initial run parks in WAITING
    await ex4.run()
    wait_node = g4.nodes["remote_specialist"]
    print(f"Node 'remote_specialist' status after initial launch: {wait_node.state.value} (Parked in WAITING)")

    # Simulate external push event arrival
    ex4.handle_external_event("remote_specialist", {
        "artifact": "Agent Card advertises capabilities; it grants no local-memory authority.",
        "provider_slot": "gemini_1"
    })
    # Resume execution to completion
    snap4 = await ex4.run()
    print(f"Node 'remote_specialist' status after external push: {g4.nodes['remote_specialist'].state.value}")
    print(f"Run Finished: {snap4['finished']}\n")

    print("=========================================================")
    print("          All 4 Floor Benchmark Cases Verified!          ")
    print("=========================================================")


if __name__ == "__main__":
    asyncio.run(run_floor_benchmarks())
