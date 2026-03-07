
from gateway.app.core.policy_engine import PolicyEngine


class TestAutoPlan:
    def test_auto_mode_routes_project_to_plan(self):
        """Project keywords -> Plan"""
        task = "plan a new project structure"
        decision = PolicyEngine.decide(task)
        assert decision.mode == "PLAN"
