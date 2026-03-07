import pytest
from unittest.mock import patch

class TestShellExecutorInit:

    @pytest.fixture
    def shell_executor(self):
        from neural_engine.shell_executor import ShellExecutor
        return ShellExecutor

    def test_happy_path(self, shell_executor):
        # Normal input
        allowed_commands = ["ls", "cat"]
        executor = shell_executor(allowed_commands)
        assert executor.allowed_commands == allowed_commands

    def test_empty_list(self, shell_executor):
        # Empty list input
        allowed_commands = []
        executor = shell_executor(allowed_commands)
        assert executor.allowed_commands == allowed_commands

    def test_none_input(self, shell_executor):
        # None input
        executor = shell_executor(None)
        assert executor.allowed_commands == ["ls", "echo", "pwd", "whoami", "date"]

    def test_invalid_input_type(self, shell_executor):
        # Invalid input type
        with pytest.raises(TypeError):
            shell_executor("not a list")

    def test_string_in_list(self, shell_executor):
        # List with string elements only
        allowed_commands = ["ls", "echo", "pwd", "whoami", "date", "uptime"]
        executor = shell_executor(allowed_commands)
        assert executor.allowed_commands == allowed_commands

    def test_mixed_types_in_list(self, shell_executor):
        # List with mixed types
        with pytest.raises(TypeError):
            shell_executor(["ls", 123, "echo"])

    def test_logger_info_called(self, shell_executor):
        # Check if logger.info is called
        allowed_commands = ["ls", "echo"]
        with patch('neural_engine.shell_executor.logger.info') as mock_logger_info:
            executor = shell_executor(allowed_commands)
            mock_logger_info.assert_called_once_with(f"ShellExecutor initialized. Allowed: {allowed_commands}")

    def test_async_behavior(self, shell_executor):
        # This function does not have async behavior to test
        pass