import pytest
from glc_v3.chunking import SemanticIndexer, Phi4SemanticSegmenter
from glc_v3.memory import MemoryService, MemoryScope, Principal


def test_rohan_v2_semantic_chunking():
    mem = MemoryService()
    indexer = SemanticIndexer(mem)
    scope = MemoryScope(tenant_id="course", project_id="s13", user_id="u1", agent_id="a1")
    principal = Principal(id="a1", role="agent")

    doc = """# Introduction to Live Graphs
Live task graphs adjust execution dynamically based on task outcomes.

# Section 2: Memory Drawers
Memory is organized into seven typed drawers with scope-first permissions.
"""

    res = indexer.index_document(doc, source_uri="file:///test.md", author="u1", scope=scope, principal=principal)
    assert res["status"] == "success"
    assert res["chunks_indexed"] > 0

    # Idempotent re-indexing test
    res2 = indexer.index_document(doc, source_uri="file:///test.md", author="u1", scope=scope, principal=principal)
    assert res2["status"] == "idempotent"
    assert res2["chunks_indexed"] == 0
