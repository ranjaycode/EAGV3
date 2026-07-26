import pytest
from glc_v3.memory import MemoryService, MemoryRecord, MemoryKind, MemoryScope, SourceRef, Principal


def test_memory_7_drawers_and_scoping():
    mem = MemoryService()
    scope_a = MemoryScope(tenant_id="course", project_id="s13", user_id="student_1", agent_id="agent_a")
    scope_b = MemoryScope(tenant_id="course", project_id="s13", user_id="student_2", agent_id="agent_b")
    principal = Principal(id="agent_a", role="agent")

    rec1 = MemoryRecord(
        id="mem_001",
        kind=MemoryKind.FACT,
        scope=scope_a,
        text="Mom's birthday is 15 May 2026.",
        sources=[SourceRef(uri="api://agent/runs", author="student_1")],
        principal=principal
    )
    mem.write_record(rec1)

    # Recall with authorized scope
    cards_a = mem.recall("birthday", scope=scope_a, kinds=[MemoryKind.FACT])
    assert len(cards_a) == 1
    assert cards_a[0].text == "Mom's birthday is 15 May 2026."

    # Recall with unauthorized scope (different user)
    cards_b = mem.recall("birthday", scope=scope_b, kinds=[MemoryKind.FACT])
    assert len(cards_b) == 0


def test_supersession_history_preservation():
    mem = MemoryService()
    scope = MemoryScope(tenant_id="course", project_id="s13", user_id="student_1", agent_id="agent_a")
    principal = Principal(id="agent_a", role="agent")

    # Initial record
    rec1 = MemoryRecord(
        id="mem_001",
        kind=MemoryKind.FACT,
        scope=scope,
        text="Mom's birthday is 15 May 2026.",
        sources=[SourceRef(uri="api://agent/runs", author="student_1")],
        principal=principal
    )
    mem.write_record(rec1)

    # Correction record superseding mem_001
    rec2 = MemoryRecord(
        id="mem_002",
        kind=MemoryKind.FACT,
        scope=scope,
        text="Mom's birthday is 16 May 2026.",
        sources=[SourceRef(uri="api://agent/runs", author="student_1")],
        principal=principal,
        supersedes_id="mem_001"
    )
    mem.write_record(rec2)

    # Normal recall only sees current
    cards = mem.recall("birthday", scope=scope, kinds=[MemoryKind.FACT])
    assert len(cards) == 1
    assert cards[0].text == "Mom's birthday is 16 May 2026."

    # Direct record inspection shows historical superseded status
    old_rec = mem.get_record("mem_001")
    assert old_rec is not None
    assert old_rec.status == "superseded"
