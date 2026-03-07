import logging
from datetime import datetime, timezone

from unified_core.intelligence.critical_thinking import CriticalThinker, Evidence

logging.basicConfig(level=logging.INFO)
critic = CriticalThinker()

def run_demo():
    print("=" * 70)
    print("DEMO 1: Detecting Cognitive Biases (Correlation vs Causation)")
    print("=" * 70)
    
    claim1 = "The server crashed because I refreshed the dashboard"
    evidence1 = [
        Evidence("I clicked refresh at 10:05", "user_action"),
        Evidence("The server went down at 10:05", "system_logs")
    ]
    reasoning1 = "Because after I clicked refresh the server crashed, it means my click caused the crash."
    
    res1 = critic.evaluate_reasoning(claim1, evidence1, reasoning1)
    
    for issue in res1['issues']:
        print(f" ✗ {issue}")
    print()

    print("=" * 70)
    print("DEMO 2: High Quality Evidence & Valid Reasoning")
    print("=" * 70)

    claim2 = "Adding the index improved query performance"
    evidence2 = [
        Evidence("Query time dropped from 500ms to 20ms", "prometheus", datetime.now(timezone.utc).isoformat()),
        Evidence("Slow query logs are empty after deployment", "elastic", datetime.now(timezone.utc).isoformat()),
        Evidence("Database CPU utilization dropped consistently across 3 instances", "aws_cloudwatch", datetime.now(timezone.utc).isoformat()),
        Evidence("Load test confirms 10x throughput", "jmeter", datetime.now(timezone.utc).isoformat()),
        Evidence("The query plan now uses an Index Scan", "postgres_explain", datetime.now(timezone.utc).isoformat())
    ]
    reasoning2 = "The addition of the index directly resulted in an Index Scan which reduced the I/O operations, leading to faster response times and lower CPU."

    res2 = critic.evaluate_reasoning(claim2, evidence2, reasoning2)

    print(f"Valid: {res2['valid']}")
    print(f"Confidence: {res2['confidence']}")
    print(f"Issues: {len(res2['issues'])}")
    print()
    
    print("=" * 70)
    print("DEMO 3: Logical Fallacies (Hasty Generalization)")
    print("=" * 70)

    claim3 = "All python scripts are broken"
    evidence3 = [
        Evidence("test_script.py failed to run", "ci_cd")
    ]
    reasoning3 = "Since one python script failed, all python scripts always fail."

    res3 = critic.evaluate_reasoning(claim3, evidence3, reasoning3)

    for issue in res3['issues']:
        print(f" ✗ {issue}")
    print()

if __name__ == "__main__":
    run_demo()
