
from gateway.app.core.capabilities import CapabilityRequirement
from gateway.app.core.policy_engine import PolicyEngine


class TestPolicyExecuteSimple:
    def test_policy_execute_simple(self):
        """Verify simple computation tasks trigger EXECUTE mode."""
        tasks = [
            "Calculate the 50th fibonacci number",
            "Execute this python script to verify logic",
            "Calculate sum of list",
            "Calculate prime numbers",
        ]

        for task in tasks:
            decision = PolicyEngine.decide(task)
            assert isinstance(decision, CapabilityRequirement)
            assert decision.mode == "EXECUTE"
            # Should have safe execution mode - reason can vary
            assert decision.reason is not None and len(decision.reason) > 0
