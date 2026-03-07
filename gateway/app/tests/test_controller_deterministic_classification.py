from unittest.mock import MagicMock


from gateway.app.core.agent_controller import AgentController
from gateway.app.core.agent_kernel import AgentKernel


class TestDeterministicClassification:
    def test_deterministic_classification(self):
        """Verify same task yields same classification."""
        mock_kernel = MagicMock(spec=AgentKernel)
        controller = AgentController(mock_kernel, secrets={"NOOGH_DATA_DIR": "/tmp/test_ctl_det"})

        task = "Analyze the codebase structure and plan a refactor for the auth module."

        # First pass - _classify_task returns CapabilityRequirement
        class1 = controller._classify_task(task)
        # Check .mode attribute
        mode1 = class1.mode if hasattr(class1, "mode") else str(class1)
        assert mode1 == "PLAN", f"Expected PLAN for planning task, got {mode1}"

        # Repeat 5 times - should be deterministic
        for _ in range(5):
            class_n = controller._classify_task(task)
            mode_n = class_n.mode if hasattr(class_n, "mode") else str(class_n)
            assert mode_n == mode1, f"Classification changed! Expected {mode1}, got {mode_n}"
