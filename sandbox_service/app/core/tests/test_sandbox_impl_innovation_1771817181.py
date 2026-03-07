import pytest
from unittest.mock import patch, MagicMock
from your_module import SandboxImpl  # Adjust this to the actual import path

class TestSandboxImpl:

    @pytest.fixture
    def sandbox_impl(self):
        client_mock = MagicMock()
        client_mock.containers.run.return_value = MagicMock(
            exec_run=MagicMock(return_value=(0, (b"stdout", b"stderr")))
        )
        return SandboxImpl(client=client_mock), client_mock

    def test_execute_code_happy_path(self, sandbox_impl):
        sandbox, _ = sandbox_impl
        result = sandbox.execute_code("print('Hello, World!')")
        assert result == {
            "success": True,
            "output": "stdout",
            "error": None,
            "exit_code": 0,
            "duration_ms": pytest.approx(10)  # Assuming a fast execution time
        }

    @patch("your_module.time")
    def test_execute_code_timeout(self, mock_time, sandbox_impl):
        sandbox, _ = sandbox_impl
        mock_time.time.side_effect = [0, 10]
        result = sandbox.execute_code("sleep(5)", timeout=2)
        assert result == {
            "success": False,
            "output": "",
            "error": f"Execution timed out after 2s",
            "exit_code": 124,
            "duration_ms": pytest.approx(2000)  # Assuming a fast execution time
        }

    def test_execute_code_empty_input(self, sandbox_impl):
        sandbox, _ = sandbox_impl
        result = sandbox.execute_code("")
        assert result == {
            "success": False,
            "output": "",
            "error": None,
            "exit_code": -1,
            "duration_ms": pytest.approx(10)  # Assuming a fast execution time
        }

    def test_execute_code_none_input(self, sandbox_impl):
        sandbox, _ = sandbox_impl
        result = sandbox.execute_code(None)
        assert result == {
            "success": False,
            "output": "",
            "error": None,
            "exit_code": -1,
            "duration_ms": pytest.approx(10)  # Assuming a fast execution time
        }

    def test_execute_code_invalid_user(self, sandbox_impl):
        sandbox, client = sandbox_impl
        client.containers.run.side_effect = docker.errors.APIError("linux spec user not found")
        with pytest.raises(RuntimeError) as exc_info:
            sandbox.execute_code("print('Hello, World!')")
        assert str(exc_info.value) == "Sandbox Security Failure: Invalid User Configuration"

    @patch("your_module.time")
    def test_execute_code_async_behavior(self, mock_time, sandbox_impl):
        sandbox, _ = sandbox_impl
        mock_time.time.side_effect = [0, 0.1]
        result = sandbox.execute_code("print('Hello, World!')")
        assert result == {
            "success": True,
            "output": "stdout",
            "error": None,
            "exit_code": 0,
            "duration_ms": pytest.approx(10)  # Assuming a fast execution time
        }