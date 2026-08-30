"""
rescore.py - Offline Rescoring Engine (No LLM Calls Needed).
Demonstrates re-evaluation of saved raw JSON journals under updated scoring rules (Scorer V1 vs V2).
"""
import json
from pathlib import Path
from harness.scorer import evaluate_all_journals, print_summary_table

def run_rescore(journals_dir: Path, results_dir: Path):
    print("\n--- Running Scorer V1 (Original Metrics) ---")
    results_v1 = evaluate_all_journals(journals_dir, version="V1")
    print_summary_table(results_v1, version="V1")

    print("\n--- Running Scorer V2 (Scoring Change: Strict Integrity Flagging) ---")
    results_v2 = evaluate_all_journals(journals_dir, version="V2")
    print_summary_table(results_v2, version="V2")

    results_dir.mkdir(parents=True, exist_ok=True)
    with open(results_dir / "scores_v1.json", "w", encoding="utf-8") as f:
        json.dump(results_v1, f, indent=2)
    with open(results_dir / "scores_v2.json", "w", encoding="utf-8") as f:
        json.dump(results_v2, f, indent=2)

    # Print Diff / Summary of changes
    print("\n[Rescore Delta Analysis]")
    changes_count = 0
    for r1, r2 in zip(results_v1, results_v2):
        if r1["outcome"] != r2["outcome"] or r1["integrity"] != r2["integrity"]:
            changes_count += 1
            print(f"Run {r1['run_id']}: V1 Outcome='{r1['outcome']}' -> V2 Outcome='{r2['outcome']}'")
    
    print(f"Rescore complete. Total reclassified runs: {changes_count}. Zero model calls were invoked!\n")

if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent
    j_dir = base_dir / "journals"
    r_dir = base_dir / "results"
    run_rescore(j_dir, r_dir)
