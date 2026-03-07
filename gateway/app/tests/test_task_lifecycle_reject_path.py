from unittest.mock import MagicMock, patch

import pytest

from gateway.app.core.agent_controller import AgentController
from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.auth import AuthContext

# Import correct RefusalResponse


class TestLifecycleReject:
    @pytest.fixture
    def controller(self):
        mock_kernel = MagicMock(spec=AgentKernel)
        return AgentController(mock_kernel, secrets={"NOOGH_DATA_DIR": "/tmp/test_life_reject"})

    def test_task_lifecycle_reject_path(self, tmp_path, controller):
        mock_brain = MagicMock()
        mock_brain.generate.return_value = "THINK: test\nACT: NONE\nREFLECT: done"

        # Initialize kernel without persistence to avoid PermissionError
        kernel = AgentKernel(brain=mock_brain, enable_persistence=False)

        # The controller fixture already provides a mock kernel.
        # We need to ensure the mock_brain is associated with the kernel
        # that the controller fixture uses, or mock the kernel's brain directly.
        # For this test, we'll mock the kernel's brain attribute.
        controller.kernel.brain = mock_brain

        # Forbidden task - should be rejected by controller before kernel
        # Mock PolicyEngine on controller
        from gateway.app.core.refusal import RefusalResponse

        with patch("gateway.app.core.agent_controller.PolicyEngine") as MockPolicyEngine:
            MockPolicyEngine.decide.return_value = RefusalResponse(
                code="ForbiddenRequest", message="Access Denied", allowed_alternatives=[]
            )

            result = controller.process_task("download internet", AuthContext(token="t", scopes={}))

            # Controller should reject it
            assert result.success is False
            assert (
                result.error
                in [
                    "ForbiddenRequest",
                    "ForbiddenCapability",
                    "CapabilityBoundaryViolation",
                    "RefusalResponse",
                    "Access Denied",
                ]
                or result.error is not None
            )

            # Kernel should NOT be called
            assert mock_brain.generate.call_count == 0
