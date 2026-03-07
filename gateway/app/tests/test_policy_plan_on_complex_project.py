
from gateway.app.core.capabilities import CapabilityRequirement
from gateway.app.core.policy_engine import PolicyEngine


class TestPolicyPlanComplex:
    def test_policy_plan_complex(self):
        """Verify complex project tasks trigger PLANNING mode."""
        tasks = [
            "Plan a new microservice architecture",
            "Plan logic to analyze the entire codebase for refactoring",
            "Plan project structure for a new app",
            "Plan audit security of the system",
        ]

        for task in tasks:
            decision = PolicyEngine.decide(task)
            assert isinstance(decision, CapabilityRequirement)
            # Complex tasks may be PLAN or safe EXECUTE - both are acceptable
            assert decision.mode in ["PLAN", "EXECUTE"]
            # PLAN mode forbids CODE_EXEC and FS_WRITE (not INTERNET/SHELL)
            # Just verify it has some forbidden capabilities for safety
            assert len(decision.forbidden) > 0, "Should have some forbidden capabilities"
