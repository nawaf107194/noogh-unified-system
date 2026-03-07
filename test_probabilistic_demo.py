import logging
from unified_core.intelligence.probabilistic import ProbabilisticReasoner, Hypothesis, EvidenceProb, ProbabilisticOption, Outcome

logging.basicConfig(level=logging.INFO)
reasoner = ProbabilisticReasoner()

def run_demo():
    print("=" * 70)
    print("DEMO 1: Bayesian Inference (Evaluating a Hypothesis under Uncertainty)")
    print("=" * 70)
    
    # Base rate (Prior): What is the historical probability the database is failing due to disk space vs logic?
    # Say disk space is a rare reason (Prior = 5%)
    hypothesis = Hypothesis("Database failed due to disk space limit", "Disk is 100% full", base_rate=0.05)
    
    # We observe two pieces of evidence
    # Evidence 1: CPU usage is completely normal (doesn't usually happen under query load max)
    ev_1 = EvidenceProb("Normal CPU", "CPU is at 10%", baseline_prob=0.8, likelihood_if_true=0.95)
    
    # Evidence 2: Syslog contains 'No space left on device' (rare overall, highly likely if disk full)
    ev_2 = EvidenceProb("Syslog Error", "No space left on device", baseline_prob=0.01, likelihood_if_true=0.99)
    
    evaluation = reasoner.evaluate_with_uncertainty(hypothesis, [ev_1, ev_2])
    print(f"Hypothesis: {evaluation['hypothesis']}")
    print(f"Prior Probability (Initial Belief): {evaluation['prior']:.2%}")
    print(f"Posterior Probability (After Evidence): {evaluation['posterior']:.2%}")
    # From 5% belief, seeing that specific syslog error should jump belief near 100%
    print("\n")

    print("=" * 70)
    print("DEMO 2: Expected Value Decision Making (Choosing an Option)")
    print("=" * 70)

    # Option 1: Roll back to previous version
    rollback_opt = ProbabilisticOption(
        name="Rollback Service V1",
        possible_outcomes=[
            Outcome("Success, service restored", probability=0.9, utility=50),
            Outcome("Schema mismatch catastrophe", probability=0.1, utility=-200) # 10% chance of disaster
        ]
    )
    
    # Option 2: Apply hotfix to V2 forward
    hotfix_opt = ProbabilisticOption(
        name="Apply Hotfix V2",
        possible_outcomes=[
            Outcome("Success, service restored", probability=0.5, utility=100), # Slower chance of working but high payoff
            Outcome("Hotfix fails, need to try another", probability=0.5, utility=-10)  # Minor penalty, but safe
        ]
    )

    # With high risk aversion, the model should prefer Hotfix despite expected utility mathematically close, to avoid the -200 outcome
    decision = reasoner.decision_under_uncertainty([rollback_opt, hotfix_opt], risk_aversion=1.5)
    
    print(f"🥇 Best Choice (Risk Adjusted): {decision['best_choice']}\n")
    print("--- Detailed Evaluations ---")
    for d in decision['evaluations']:
        print(f"Option: {d['option']}")
        print(f"   Expected Value (Utility): {d['expected_value']:.2f}")
        print(f"   Standard Deviation (Volatility): {d['standard_deviation']:.2f}")
        print(f"   Catastrophic Risk Probability: {d['catastrophic_risk_prob']:.2%}")
        print(f"   Final Risk-Adjusted Score: {d['risk_adjusted_score']:.2f}\n")

if __name__ == "__main__":
    run_demo()
