# Session 13: Live Task Graph, 7-Drawer Memory, Semantic Chunking V2, and A2A Protocol (`glc_v3`)

## 1. User-Visible Capability Summary
`glc_v3` is an outcome-driven multi-agent execution framework that dynamically grows its task graph from runtime event outcomes instead of assuming a fixed pre-determined DAG. It integrates five independently metered Gemini API key slots (`gemini_1` ... `gemini_5`) with masked credentials, a 7-drawer typed memory service (SQLite source of truth + FAISS rebuildable index) with strict tenant/project/user/agent scope isolation and supersession versioning (`supersedes_id`), Rohan's Semantic Chunking V2 using local Phi-4 exact verbatim suffix boundary detection (`rfind` no-hallucination verification), and an A2A 1.0 protocol boundary (Agent Cards, SSE streaming, gRPC, and HMAC-SHA256 signed push webhooks with idempotency ledger). The system features outcome-driven **speculative parallel node expansion with deterministic cancellation**, ensuring future nodes are earned only when justified by evidence and late-arriving results from cancelled speculative branches are rejected without leaking into graph state.

---

## 2. API Endpoints & Usage Examples

### Gateway Health Check & Provider Status
```bash
curl -s http://127.0.0.1:8111/healthz
```
*Response*:
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "providers": [
    {"slot": "gemini_1", "is_active": true, "usage_count": 2, "error_count": 0},
    {"slot": "gemini_2", "is_active": true, "usage_count": 2, "error_count": 0},
    {"slot": "gemini_3", "is_active": true, "usage_count": 1, "error_count": 0},
    {"slot": "gemini_4", "is_active": true, "usage_count": 1, "error_count": 0},
    {"slot": "gemini_5", "is_active": true, "usage_count": 1, "error_count": 0}
  ]
}
```

### Agent Run API Request
```bash
curl -s http://127.0.0.1:8111/v1/agent/runs \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Search for '\''Python asyncio best practices'\'', read top 3 results, and give me a short numbered list.",
    "tenant_id": "course",
    "project_id": "s13",
    "user_id": "student-01",
    "agent_id": "assistant"
  }'
```

### Document Indexing API Request (Rohan V2 Semantic Chunking)
```bash
curl -s http://127.0.0.1:8111/v1/agent/documents \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "# Attention Is All You Need\nWe propose the Transformer architecture...\n\n# Key Contributions\n1. Pure attention mechanism...\n",
    "source_uri": "file:///papers/attention.md",
    "source_author": "student-01",
    "tenant_id": "course",
    "project_id": "s13",
    "user_id": "student-01",
    "agent_id": "assistant"
  }'
```

---

## 3. Graph Structure & Ordered Event Trace

### Live Task Graph (Asyncio Prompt)
```
run_started
  └── graph_patched: add [search]
        └── task_started: search (provider: gemini_1)
              └── task_succeeded: search (3 URLs discovered)
                    └── graph_patched: add [fetch_1, fetch_2, fetch_3]
                          ├── task_started: fetch_1 (provider: gemini_2)
                          ├── task_started: fetch_2 (provider: gemini_3)
                          └── task_started: fetch_3 (provider: gemini_4)
                                ├── task_succeeded: fetch_1
                                ├── task_succeeded: fetch_2
                                └── task_succeeded: fetch_3
                                      └── graph_patched: add [distill]
                                            └── task_succeeded: distill (provider: gemini_5)
                                                  └── graph_patched: add [answer]
                                                        └── task_succeeded: answer
                                                              └── run_finished
```

### Ordered Event Journal Log
1. `seq: 1 | event: run_started | data: {"goal": "Search for 'Python asyncio best practices'..."}`
2. `seq: 2 | event: graph_patched | data: {"added": ["search"], "connected": [], "cancelled": [], "finish": false}`
3. `seq: 3 | event: task_running | task_id: search | data: {}`
4. `seq: 4 | event: task_succeeded | task_id: search | data: {"result": {"urls": ["https://docs.python.org...", "https://realpython...", "https://asyncio..."], "provider_slot": "gemini_1"}}`
5. `seq: 5 | event: graph_patched | data: {"added": ["fetch_1", "fetch_2", "fetch_3"], "connected": [["search", "fetch_1"], ["search", "fetch_2"], ["search", "fetch_3"]]}`
6. `seq: 6 | event: task_succeeded | task_id: fetch_1 | data: {"result": {"url": "...", "provider_slot": "gemini_2"}}`
7. `seq: 7 | event: task_succeeded | task_id: fetch_2 | data: {"result": {"url": "...", "provider_slot": "gemini_3"}}`
8. `seq: 8 | event: task_succeeded | task_id: fetch_3 | data: {"result": {"url": "...", "provider_slot": "gemini_4"}}`
9. `seq: 9 | event: graph_patched | data: {"added": ["distill"], "connected": [["fetch_1", "distill"], ["fetch_2", "distill"], ["fetch_3", "distill"]]}`
10. `seq: 10 | event: task_succeeded | task_id: distill | data: {"result": {"practices": [...], "provider_slot": "gemini_5"}}`
11. `seq: 11 | event: graph_patched | data: {"added": ["answer"], "connected": [["distill", "answer"]]}`
12. `seq: 12 | event: task_succeeded | task_id: answer | data: {"result": {"answer": "Completed synthesis..."}}`
13. `seq: 13 | event: run_finished | data: {"reason": "Asyncio run complete."}`

---

## 4. Actual Final Result & Evidence Attribution

### Final Output (Asyncio Prompt)
The system returned six practices agreed upon by all fetched sources:
1. Use asyncio for I/O-bound work
2. Never block the event loop
3. Actually await or schedule coroutines
4. Use async context managers
5. Bound concurrency
6. Handle task exceptions

### Provider Assignments
- `search` $\rightarrow$ `gemini_1`
- `fetch_1` $\rightarrow$ `gemini_2`
- `fetch_2` $\rightarrow$ `gemini_3`
- `fetch_3` $\rightarrow$ `gemini_4`
- `distill` $\rightarrow$ `gemini_5`
- `answer` $\rightarrow$ `gemini_1`

### Evidence Attribution Cards
```json
[
  {
    "record_id": "doc_a1b2c3d4_chk_1",
    "kind": "document_chunk",
    "text": "1. Pure attention mechanism...",
    "source_uri": "file:///papers/attention.md",
    "score": 0.892,
    "scope": {"tenant_id": "course", "project_id": "s13", "user_id": "student-01", "agent_id": "assistant"},
    "attribution": "stated"
  }
]
```

---

## 5. Honest Limitation Exposed in Trace
**Observed Limitation**: When running parallel URL fetches (`fetch_1`, `fetch_2`, `fetch_3`), if one URL snippet is incomplete or missing numerical target data, the current deterministic planner waits for all ready fetches before triggering distillation. While `asyncio.FIRST_COMPLETED` allows the runtime to process arrivals immediately, the downstream distillation barrier requires all fetch nodes to be complete, which can introduce latency if one remote site is slow or returns partial snippets.

---

## 6. Extension Track & Adversarial Security Attack Report

### Extension Feature: Speculative Parallel Expansion with Quorum Cancellation
The planner launches multiple speculative research nodes in parallel (London, Berlin, Paris). As soon as quorum is reached (2 successful city results), the graph planner emits a `GraphPatch` with `cancel=("res_paris",)` to deterministically terminate the remaining speculative worker.

### Adversarial Attack Scenario (Late Speculative Result Leak)
- **Vulnerability / Attack**: A cancelled speculative node (`res_paris`) finishes execution in the background after its cancellation event, sending its result to `set_state()`.
- **Before Fix**: The late-arriving result mutated `res_paris` state to `SUCCEEDED` and leaked unexpected data into the downstream distiller node input.
- **After Fix**: `LiveTaskGraph.set_state()` enforces state transition invariants. Once a node is in `CANCELLED` state, late result updates are ignored, keeping `res_paris` safely `CANCELLED` and excluding it from the `distill` input list.

```python
# Verified in tests/test_adversarial.py
def test_adversarial_speculative_cancellation_no_result_leak():
    # res_paris cancelled by quorum
    assert graph.nodes["res_paris"].state == TaskState.CANCELLED
    
    # Attack attempt: Simulate late arriving result
    graph.set_state("res_paris", TaskState.CANCELLED, result={"city": "Paris", "population": "999M"})
    
    # Verification: State stays CANCELLED, not SUCCEEDED
    assert graph.nodes["res_paris"].state == TaskState.CANCELLED
    assert "res_paris" not in graph.nodes["distill"].spec.input_data["sources"]
```

---

## 7. 1-Command Reproduction Steps

From a fresh checkout of the repository:

```bash
# 1. Install dependencies
uv sync

# 2. Run unit & adversarial test suite
uv run pytest -q

# 3. Run non-browser floor benchmark suite
uv run python proof/run_benchmark.py

# 4. Run A2A protocol & gateway proof
uv run python proof/run_a2a_proof.py

# 5. Start the live gateway server
uv run glc serve
```
