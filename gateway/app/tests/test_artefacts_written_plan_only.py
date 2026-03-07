import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from gateway.app.core.agent_controller import AgentController
from gateway.app.core.agent_kernel import AgentKernel  # Added import for AgentKernel
from gateway.app.core.auth import AuthContext


class TestArtifactsPlan:
    # @pytest.mark.skip(reason="Plan artifact writing not yet implemented")
    @pytest.fixture
    def controller_fixture(self):  # Renamed fixture to avoid conflict with local variable
        mock_kernel = MagicMock(spec=AgentKernel)
        mock_kernel.process.return_value = MagicMock(success=True, answer="# My Plan", steps=0, metadata={})
        # The secrets dict is injected here
        return AgentController(mock_kernel, secrets={})

    def test_artefacts_written_plan_only(self, controller_fixture):  # Modified to accept fixture
        # mock_kernel and controller initialization moved to fixture
        # mock_kernel = MagicMock()
        # mock_kernel.process.return_value = MagicMock(success=True, answer="# My Plan", steps=0, metadata={})

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"NOOGH_DATA_DIR": temp_dir}):
                # controller = AgentController(mock_kernel) # Use the fixture instead
                controller = AgentController(controller_fixture.kernel, secrets={"NOOGH_DATA_DIR": temp_dir})
                result = controller.process_task("plan feature", AuthContext(token="t", scopes={"*"}))

                task_id = result.metadata["task_id"]
                path = os.path.join(temp_dir, ".noogh_memory", "tasks", task_id, "plan.md")
                assert os.path.exists(path)
                with open(path) as f:
                    assert "# My Plan" in f.read()
