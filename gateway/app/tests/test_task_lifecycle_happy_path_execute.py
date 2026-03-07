from unittest.mock import MagicMock

import pytest

from gateway.app.core.agent_controller import AgentController
from gateway.app.core.agent_kernel import AgentKernel  # Added import for AgentKernel
from gateway.app.core.auth import AuthContext


class TestLifecycleExecute:
    @pytest.fixture
    def controller(self):
        mock_kernel = MagicMock(spec=AgentKernel)
        mock_kernel.process.return_value = MagicMock(success=True, answer="Done", steps=1, metadata={})
        return AgentController(mock_kernel, secrets={"NOOGH_DATA_DIR": "/tmp/test_life_exec"})

    def test_task_lifecycle_happy_path_execute(self, controller):  # Modified to accept controller fixture
        # Use simple execute trigger
        result = controller.process_task("calculate sum", AuthContext(token="t", scopes={"*"}))

        meta = result.metadata
        lifecycle = meta["lifecycle"]

        assert "RECEIVED" in lifecycle[0] or "RECEIVED" == lifecycle[0]
        assert any("EXECUTED" in s for s in lifecycle)
        assert any("COMPLETED" in s for s in lifecycle)
        # assert "report.md" in meta["artefacts"]
