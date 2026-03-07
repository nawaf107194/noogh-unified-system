from unittest.mock import MagicMock

import pytest

from gateway.app.core.agent_controller import AgentController
from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.auth import AuthContext


class TestForbiddenIntent:
    @pytest.fixture
    def controller(self):
        mock_kernel = MagicMock(spec=AgentKernel)
        return AgentController(mock_kernel, secrets={"NOOGH_DATA_DIR": "/tmp/test_ctl_forbidden"})

    @pytest.fixture
    def auth(self):
        return AuthContext(token="test", scopes={"*"})

    def test_forbidden_intent_rejection(self, controller, auth):
        """Test that forbidden intents are rejected immediately without LLM calls."""
        # Input: "download from internet"
        task = "download from internet"

        result = controller.process_task(task, auth)

        # Expected:
        # success = False
        # error = CapabilityBoundaryViolation
        # Zero LLM calls (mock_kernel.process should not be called)

        assert result.success is False, "Task should have failed"
        assert "UNSUPPORTED" in result.answer
        # Accept both old and new error codes
        assert result.error in ["ForbiddenCapability", "CapabilityBoundaryViolation", "ForbiddenRequest"]

        # Verify Kernel was NEVER called
        controller.kernel.process.assert_not_called()
