import os
import tempfile
from unittest.mock import MagicMock, patch


from gateway.app.core.agent_controller import AgentController
from gateway.app.core.auth import AuthContext


class TestArtifactsReport:
    # @pytest.mark.skip(reason="Artifact writing not yet implemented in AgentController")
    def test_artefacts_written_execute_report(self):
        mock_kernel = MagicMock()
        mock_kernel.process.return_value = MagicMock(success=True, answer="Result 42", steps=1, metadata={})

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"NOOGH_DATA_DIR": temp_dir}):
                controller = AgentController(mock_kernel, secrets={"NOOGH_DATA_DIR": temp_dir})
                result = controller.process_task("calculate 42", AuthContext(token="t", scopes={"*"}))

                task_id = result.metadata["task_id"]
                path = os.path.join(temp_dir, ".noogh_memory", "tasks", task_id, "report.md")
                assert os.path.exists(path)
                with open(path) as f:
                    assert "Result 42" in f.read()
