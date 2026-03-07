
from gateway.app.core.capabilities import Capability, CapabilityRequirement
from gateway.app.core.policy_engine import PolicyEngine
from gateway.app.core.refusal import RefusalResponse


class TestAutoFailClosed:
    def test_auto_mode_fail_closed_ambiguous(self):
        """Ambiguous -> Safe mode with restrictions"""
        task = "hello world"
        decision = PolicyEngine.decide(task)

        # Accept both RefusalResponse or CapabilityRequirement with safe defaults
        assert isinstance(decision, (RefusalResponse, CapabilityRequirement))

        if isinstance(decision, CapabilityRequirement):
            # Should be EXECUTE mode with forbidden dangerous capabilities
            assert decision.mode == "EXECUTE"
            assert Capability.INTERNET in decision.forbidden
            assert Capability.SHELL in decision.forbidden
        elif isinstance(decision, RefusalResponse):
            assert decision.code == "AmbiguousIntent"
