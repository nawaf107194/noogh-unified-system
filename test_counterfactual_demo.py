import logging
from unified_core.intelligence.counterfactual import CounterfactualReasoner, CognitiveState, SimulatedOutcome, DecisionAlternative, DecisionPoint

logging.basicConfig(level=logging.INFO)
reasoner = CounterfactualReasoner()

def run_demo():
    print("=" * 70)
    print("DEMO 1: Missing an Opportunity (What if we scaled instead?)")
    print("=" * 70)
    
    # State: A massive traffic spike hitting 95% CPU
    state_spike = CognitiveState("2026-02-25T11:00:00Z", {"cpu_usage": 95.0, "latency": 800.0}, "Sudden traffic spike identified.")
    
    # Alternatives present at the time
    alt_ignore = DecisionAlternative("Ignore/Do nothing", "Wait for traffic to subside")
    alt_scale = DecisionAlternative("Scale up load balancers", "Spin up 2 new worker nodes")
    alt_restart = DecisionAlternative("Restart services", "Flush memory aggressively")
    
    # What did we actually do?
    chosen_action = alt_restart
    
    # How did it actually turn out?
    # Say we restarted, but it took down the system slightly and the users disconnected.
    actual_outcome = SimulatedOutcome(
        description="Services restarted. Users briefly disconnected, spike mitigated, but 50% checkout drop.",
        utility=30.0,
        side_effects=["Downtime (30s)", "Dropped active carts"]
    )
    
    decision_past = DecisionPoint(
        id="DP-1049A",
        state=state_spike,
        alternatives=[alt_ignore, alt_scale, alt_restart],
        chosen=chosen_action,
        rationale="Thought it was a memory leak, opted to clear RAM fast."
    )
    
    counterfactuals = reasoner.generate_counterfactuals(actual_outcome, decision_past)
    lessons = reasoner.learn_from_counterfactuals(counterfactuals)

    print(f"Historical Incident: {decision_past.state.description}")
    print(f"Chosen Action: {chosen_action.name}")
    print(f"Actual Result: Utility = {actual_outcome.utility}, Desc = '{actual_outcome.description}'\n")
    
    print("--- 🧠 Counterfactual Generation ('What If') ---")
    for cf in counterfactuals:
        print(f"What if we had chosen '{cf['alternative']}'?")
        print(f"   Predicted Result: {cf['predicted_outcome'].description}")
        print(f"   Utility Difference: {cf['comparison']['utility_diff']:+.1f}")
        print(f"   New Side Effects: {cf['comparison']['new_side_effects']}")
        print(f"   {cf['lesson_learned']}\n")

    print("\n--- 📝 Distilled Lessons Logged to Cognitive Journal ---")
    for lesson in lessons:
        if lesson['type'] == 'MISSED_OPPORTUNITY':
             print(f"[MISS] We should favor '{lesson['action_to_favor_future']}' next time. Lost utility: {lesson['lost_utility']}")
        else:
             print(f"[VALIDATED] Thank god we avoided '{lesson['action_to_avoid_future']}'. Saved utility: {lesson['saved_utility']}")
             
if __name__ == "__main__":
    run_demo()
