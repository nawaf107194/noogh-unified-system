
from gateway.app.core.capabilities import Capability, CapabilityRequirement
from gateway.app.core.policy_engine import PolicyEngine
from gateway.app.core.refusal import RefusalResponse


class TestPolicyFailClosed:
    def test_policy_fail_closed_ambiguous(self):
        """Verify ambiguous tasks result in safe mode (Fail-Closed)."""
        tasks = ["hello", "what's up", "do something cool", "make it better"]

        for task in tasks:
            decision = PolicyEngine.decide(task)
            # Accept both RefusalResponse or safe CapabilityRequirement
            assert isinstance(decision, (RefusalResponse, CapabilityRequirement))

            if isinstance(decision, CapabilityRequirement):
                # Must have dangerous capabilities forbidden
                assert Capability.INTERNET in decision.forbidden
                assert Capability.SHELL in decision.forbidden
