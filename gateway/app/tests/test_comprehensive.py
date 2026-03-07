import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from gateway.app.main import app

client = TestClient(app, raise_server_exceptions=False)


class TestV041Stability:
    """Stability tests for v0.4.1 Hardened System"""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        os.environ["NOOGH_SERVICE_TOKEN"] = "test-token"

    def test_health_auth(self):
        import asyncio
        from unittest.mock import MagicMock

        from gateway.app.api.routes import health_check

        mock_request = MagicMock()
        mock_request.app.state.secrets = {}
        # We need to mock get_controller to return something, otherwise health_check returns 'starting'
        with patch("gateway.app.api.routes.get_controller", return_value=MagicMock()):
            result = asyncio.run(health_check(mock_request))
            assert result["status"] == "ok"

    def test_health_no_auth(self):
        import asyncio
        from unittest.mock import MagicMock

        from gateway.app.api.routes import health_check

        mock_request = MagicMock()
        mock_request.app.state.secrets = {}
        with patch("gateway.app.api.routes.get_controller", return_value=MagicMock()):
            result = asyncio.run(health_check(mock_request))
            assert result["status"] == "ok"

    def test_task_execution_flow(self):
        os.environ["NOOGH_DATA_DIR"] = "/tmp/noogh_test_data"
        os.makedirs("/tmp/noogh_test_data/.noogh_memory/sessions", exist_ok=True)
        os.makedirs("/tmp/noogh_test_data/.noogh_audit", exist_ok=True)

        with patch("gateway.app.api.routes.get_controller") as mock_controller_getter:
            mock_controller = MagicMock()
            from gateway.app.core.agent_kernel import AgentResult

            mock_controller.process_task.return_value = AgentResult(success=True, answer="Done", steps=1)
            mock_controller.kernel = MagicMock()
            mock_controller.kernel.max_iterations = 10
            mock_controller_getter.return_value = mock_controller

            from gateway.app.api.routes import TaskRequest, UnifiedResponse, process_task

            req = TaskRequest(task="Say hello")

            class DummyClient:
                host = "127.0.0.1"

            class DummyRequest:
                def __init__(self):
                    self.headers = {}
                    self.url = "http://testserver"
                    self.app = MagicMock()
                    self.app.state.secrets = {"NOOGH_DATA_DIR": "/tmp/noogh_test_data"}
                    self.client = DummyClient()

                def get(self, key, default=None):
                    return self.headers.get(key, default)

            class DummyAuth:
                pass

            with patch("gateway.app.api.routes.is_mfa_verified", return_value=False):
                result = process_task(req, DummyRequest(), DummyAuth())

            assert isinstance(result, UnifiedResponse)
            assert result.answer == "Done"
            assert result.success is True

    def test_ast_validation_blocking(self):
        from gateway.app.core.ast_validator import validate_python

        res = validate_python("import os; os.system('ls')")
        assert res.ok is False
        assert "Forbidden module referenced: os" in res.reasons

    def test_budget_io_read(self):
        # Create a small file
        import tempfile

        from gateway.app.core.agent_kernel import AgentKernel

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write("1234567890")
            path = tmp.name

        parent_dir = os.path.dirname(path)

        # Initialize kernel with specific data_dir to enforce safe root
        kernel = AgentKernel(brain=MagicMock(), data_dir=parent_dir)
        kernel.budget.max_bytes_read = 5

        try:
            res = kernel.tools._read_file(path)
            assert "Read budget exceeded" in res.get("error", "")
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
