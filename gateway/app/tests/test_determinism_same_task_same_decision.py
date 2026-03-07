
from gateway.app.core.policy_engine import PolicyEngine


class TestDeterminism:
    def test_determinism_same_task(self):
        """Verify PolicyEngine produces identical results for same input."""
        task = "calculate sum of [1,2,3]"

        decision1 = PolicyEngine.decide(task)

        for _ in range(10):
            decision_n = PolicyEngine.decide(task)
            assert decision_n == decision1
            assert decision_n.mode == decision1.mode
