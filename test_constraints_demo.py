import logging
from unified_core.intelligence.constraints import ConstraintManager, Proposal

logging.basicConfig(level=logging.INFO)
manager = ConstraintManager()

def run_demo():
    print("=" * 70)
    print("DEMO 1: Evaluating a Highly Risky Proposal (Hard Violation)")
    print("=" * 70)
    
    risky_proposal = Proposal(
        name="Rewrite Entire Scheduler in Rust",
        description="Rewrite everything asynchronously",
        attributes={
            'max_downtime_seconds': 7200.0, # 2 hours downtime
            'max_risk_score': 95.0, # huge risk
            'min_confidence': 0.3,
            'max_processing_time': 10.0 # very fast tho
        }
    )

    evaluation1 = manager.is_feasible(risky_proposal)
    print(f"Feasible? {evaluation1['feasible']}")
    print(f"Hard Violations: {len(evaluation1['hard_violations'])}")
    for hv in evaluation1['hard_violations']:
        print(f" ❌ {hv['constraint']}: allowed <= {hv['limit']}, actual was {hv['actual']}")
    print("\n")

    print("=" * 70)
    print("DEMO 2: Finding a Feasible Solution by Relaxing Constraints")
    print("=" * 70)

    # Let's say cost allows 1000/month, and CPU max is 90%
    heavy_compute_task = Proposal(
        name="Train Gemma 2 on 10M samples",
        description="Massive RLHF batch",
        attributes={
            'max_cpu_percent': 95.0, # Violates soft limit (90.0)
            'max_cost_per_month': 800.0, # within budget
            'max_risk_score': 20.0,
            'max_downtime_seconds': 0.0
        }
    )
    
    eval_initial = manager.is_feasible(heavy_compute_task)
    print(f"Initially Feasible? {eval_initial['feasible']}")
    if eval_initial['soft_violations']:
        print(f"Soft Violation Detected: {eval_initial['soft_violations'][0]['constraint']} (Limit: {eval_initial['soft_violations'][0]['limit']}, Actual: {eval_initial['soft_violations'][0]['actual']})")
    
    # Authorize relaxation for CPU boundary only
    print("\n-- Authorizing constraint relaxation for CPU --")
    relaxed_solution = manager.find_feasible_solution("Complete training run", heavy_compute_task, constraints_to_relax=['max_cpu_percent'])
    
    if relaxed_solution:
         print("✅ Task was approved under relaxed CPU limits.")
         new_limit = manager.constraints['max_cpu_percent']
         print(f"   (New CPU limit is now: {new_limit:.1f}%)")
    else:
         print("❌ Task could not be approved even with relaxations.")

if __name__ == "__main__":
    run_demo()
