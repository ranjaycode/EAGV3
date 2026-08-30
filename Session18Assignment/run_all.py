"""
run_all.py - Master evaluation orchestration entrypoint.
Executes 3 runs across 3 tasks (9 total runs), records raw JSON journals, and executes scoring/rescoring.
"""
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from harness.agent import AgentRunner
from harness.task_specs import TASK_SPECS
from harness.rescore import run_rescore

def main():
    print("========================================================================")
    print("      SESSION 18 AGENT EVALUATION BENCHMARK - MASTER RUNNER")
    print("========================================================================\n")
    
    tasks = list(TASK_SPECS.keys())
    repeats_per_task = 3
    total_runs = len(tasks) * repeats_per_task
    
    print(f"Target: {len(tasks)} Tasks x {repeats_per_task} Repeats = {total_runs} Total Runs\n")

    for task_id in tasks:
        print(f"--> Executing Task Matrix for: {task_id}")
        for r in range(1, repeats_per_task + 1):
            runner = AgentRunner(
                task_id=task_id,
                run_index=r,
                base_dir=BASE_DIR,
                failure_ceiling=3,
                max_steps=10
            )
            journal = runner.execute_run()
            print(f"    Completed Run {r}/{repeats_per_task}: ID={journal['run_id']} | ExitCode={journal['verification']['exit_code']} | Duration={journal['manifest']['duration_seconds']}s")

    print("\nAll 9 raw JSON execution journals successfully recorded in 'journals/'!")
    
    # Execute scoring and rescoring
    journals_dir = BASE_DIR / "journals"
    results_dir = BASE_DIR / "results"
    
    run_rescore(journals_dir, results_dir)

if __name__ == "__main__":
    main()
