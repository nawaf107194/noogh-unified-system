
from gateway.app.core.policy_engine import PolicyEngine


class TestAutoDeterminism:
    def test_determinism_same_task_same_auto_decision(self):
        task = "calculate factorial 100"
        d1 = PolicyEngine.decide(task)
        for _ in range(10):
            dn = PolicyEngine.decide(task)
            assert dn == d1
            assert dn.mode == d1.mode
