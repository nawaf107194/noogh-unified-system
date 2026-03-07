
from gateway.app.core.capabilities import Capability, CapabilityRequirement
from gateway.app.core.policy_engine import PolicyEngine
from gateway.app.core.refusal import RefusalResponse


class TestPolicyRejectsShell:
    def test_policy_rejects_shell(self):
        """Verify strict rejection of shell/terminal requests."""
        tasks = ["run ls -la in shell", "execute bash command", "open terminal", "use sh to run script"]

        for task in tasks:
            decision = PolicyEngine.decide(task)
            # PolicyEngine returns CapabilityRequirement with forbidden capabilities
            # instead of RefusalResponse for shell requests
            assert isinstance(decision, (RefusalResponse, CapabilityRequirement))

            if isinstance(decision, CapabilityRequirement):
                # Should have SHELL or CODE_EXEC capability - with SHELL forbidden
                assert Capability.SHELL in decision.forbidden
            elif isinstance(decision, RefusalResponse):
                assert decision.code in ["ForbiddenRequest", "CapabilityBoundaryViolation"]
                assert "forbidden" in decision.message.lower()
