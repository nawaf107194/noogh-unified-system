
from gateway.app.core.policy_engine import PolicyEngine


class TestAutoExec:
    def test_auto_mode_routes_low_complexity_to_execute(self):
        """Low complexity + compute keywords -> Execute"""
        task = "calculate sum of list"  # < 50 words, has keywor
        decision = PolicyEngine.decide(task)
        assert decision.mode == "EXECUTE"
