from unified_core.intelligence.explainer import Explainer, Decision, Alternative

def run_demo():
    explainer = Explainer()

    # Setup a mock decision
    decision = Decision(
        trigger="System memory reached 92%, triggering OOM risk alert.",
        action="Scale up the worker pool by adding 2 new nodes.",
        reasoning_steps=[
            "Verified memory spike was not due to a memory leak.",
            "Historical data shows memory spikes during this time frame persist for 2 hours.",
            "Current node count is insufficient to handle the queue depth.",
            "Adding 2 nodes will distribute the load and drop average memory to ~65%."
        ],
        selection_reason="Fastest mitigation with highest certainty of preventing downtime.",
        alternatives=[
            Alternative(
                name="Restart Services",
                description="Kill and restart memory-intensive tasks.",
                rejection_reason="Would cause task failure and interrupt user pipelines."
            ),
            Alternative(
                name="Do Nothing",
                description="Wait and see if memory drops.",
                rejection_reason="Too risky given the 92% utilization and 15 minute warning window."
            )
        ],
        evidence_quality=0.9,
        strategy_success_rate=0.95,
        risk_score=10,
        confidence=0.92,
        risks=[
            "Slight increase in cloud billing for the remainder of the hour.",
            "Possible race condition during node initialization (low probability)."
        ],
        next_steps=[
            "Monitor memory usage on new nodes to ensure load balancing is active.",
            "Schedule a scale-down event in 3 hours if queue drops below threshold."
        ]
    )

    print("\n" + "*"*80)
    print("1. TECHNICAL AUDIENCE")
    print("*"*80)
    print(explainer.explain_decision(decision, audience="technical"))

    print("\n" + "*"*80)
    print("2. EXECUTIVE AUDIENCE")
    print("*"*80)
    print(explainer.explain_decision(decision, audience="executive"))

    print("\n" + "*"*80)
    print("3. USER AUDIENCE")
    print("*"*80)
    print(explainer.explain_decision(decision, audience="user"))

    print("\n" + "*"*80)
    print("4. METACOGNITIVE SELF-EXPLANATION")
    print("*"*80)
    self_thinking = {
        "what_i_did": "Evaluated the OOM risk and elected to scale up nodes rather than killing tasks.",
        "why_i_did_it": "User continuity is prioritized higher than minor, temporary infrastructure cost increases.",
        "what_i_learned": "Our current scale-up response is fast enough to beat the 15-minute OOM window.",
        "what_id_do_differently": "Next time, I should check if the queue depth is artificial (e.g. from an API retry loop) before scaling."
    }
    print(explainer.explain_to_self(self_thinking))

if __name__ == "__main__":
    run_demo()
