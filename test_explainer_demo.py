import logging
from unified_core.intelligence.explainer import Explainer, Decision, Alternative

logging.basicConfig(level=logging.INFO)
explainer = Explainer()

def run_demo():
    print("=" * 70)
    print("DEMO 1: Explain Technical Decision")
    print("=" * 70)
    
    technical_decision = Decision(
        trigger="Query taking 120ms with sequential scan on big table",
        action="Add composite index to timestamp and user_id columns",
        reasoning_steps=[
            "Data size exceeded 50M rows",
            "Sequential scan forces full table read taking ~110ms alone",
            "Queries filter primarily by user_id and sort by timestamp",
            "Building index will take 4 minutes of slight lag but block nothing",
        ],
        selection_reason="Fastest way to eliminate seq-scan and utilize index-only scan",
        alternatives=[
            Alternative(
                name="Partitioning table",
                description="Split table by month",
                rejection_reason="Too invasive for current schema and requires application downtime"
            ),
            Alternative(
                name="Cache results",
                description="Put Redis layer in front",
                rejection_reason="Data is highly realtime, cache invalidation would be too complex"
            )
        ],
        evidence_quality=0.9,
        strategy_success_rate=0.95,
        risk_score=10,
        confidence=0.92,
        risks=["Slight write penalty during index creation", "Consumes extra 2GB disk space"],
        next_steps=["Run CREATE INDEX CONCURRENTLY", "Monitor replication lag", "Verify EXPLAIN ANALYZE output"]
    )

    print(explainer.explain_decision(technical_decision, audience='technical'))
    print("\n")
    
    print("=" * 70)
    print("DEMO 2: Explain to Executive")
    print("=" * 70)
    
    print(explainer.explain_decision(technical_decision, audience='executive'))
    print("\n")

    print("=" * 70)
    print("DEMO 3: Self-Explanation (Metacognitive rubber ducking)")
    print("=" * 70)
    
    thoughts = {
        'what_i_did': "Analyzed the DB lag and injected an optimization task into the Evolution Manager.",
        'why_i_did_it': "The system health monitor triggered a warning for latency spikes above 100ms.",
        'what_i_learned': "Next time I should check the table size first, as adding an index blocks slightly on large tables without the CONCURRENTLY flag.",
        'what_id_do_differently': "I will automatically append CONCURRENTLY to all future DB index proposals to prevent write blocking."
    }

    print(explainer.explain_to_self(thoughts))
    print("\n")

if __name__ == "__main__":
    run_demo()
