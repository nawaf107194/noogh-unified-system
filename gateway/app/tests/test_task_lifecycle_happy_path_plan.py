from unittest.mock import MagicMock

import pytest

from gateway.app.core.agent_controller import AgentController
from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.auth import AuthContext


class TestLifecyclePlan:
    @pytest.fixture
    def controller(self):
        mock_kernel = MagicMock(spec=AgentKernel)
        mock_kernel.process.return_value = MagicMock(success=True, answer="Plan", steps=0, metadata={})
        return AgentController(mock_kernel, secrets={"NOOGH_DATA_DIR": "/tmp/test_life_plan"})

    def test_task_lifecycle_happy_path_plan(self, controller):
        # Use plan trigger
        result = controller.process_task("plan project refactor", AuthContext(token="t", scopes={"*"}))

        meta = result.metadata
        lifecycle = meta["lifecycle"]

        assert any("PLANNED" in s for s in lifecycle)
        assert any("COMPLETED" in s for s in lifecycle)
        # assert "plan.md" in meta["artefacts"]
