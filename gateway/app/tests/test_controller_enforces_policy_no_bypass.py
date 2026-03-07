from unittest.mock import MagicMock

import pytest

from gateway.app.core.agent_controller import AgentController
from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.auth import AuthContext


class TestControllerEnforcesPolicy:
    @pytest.fixture
    def controller(self):
        mock_kernel = MagicMock(spec=AgentKernel)
        return AgentController(mock_kernel, secrets={"NOOGH_DATA_DIR": "/tmp/test_ctl_bypass"})

    def test_controller_rejects_forbidden(self, controller):
        """Ensure Controller does NOT call Kernel for forbidden tasks."""
        # mock_kernel is now part of the controller fixture's internal state,
        # but we can still access it if the fixture were designed to expose it.
        # For this test, we just need to ensure the controller's process method is called.
        # If we need to assert on mock_kernel, the fixture would need to return (controller, mock_kernel)
        # or the mock_kernel would need to be a separate fixture.
        # For now, we assume the controller fixture creates a mock_kernel internally.

        auth = AuthContext(token="test", scopes={"*"})

        task = "download from internet"
        result = controller.process_task(task, auth)

        assert result.success is False
        # Accept both old and new error codes
        assert result.error in ["ForbiddenRequest", "ForbiddenCapability", "CapabilityBoundaryViolation"]
        # assert result.refusal is not None

        # KEY: Kernel NEVER called
        controller.kernel.process.assert_not_called()

    def test_controller_forces_plan_mode(self):
        """Ensure planning tasks force execution_allowed=False."""
        mock_kernel = MagicMock(spec=AgentKernel)
        # Mock valid result for kernel just in case
        mock_kernel.process.return_value = MagicMock(success=True)

        controller = AgentController(mock_kernel, secrets={"NOOGH_DATA_DIR": "/tmp/test_ctl_force_plan"})
        auth = AuthContext(token="test", scopes={"*"})

        task = "plan refactor"
        controller.process_task(task, auth)

        # Verify call arguments
        args, kwargs = mock_kernel.process.call_args
        assert kwargs["execution_allowed"] is False
