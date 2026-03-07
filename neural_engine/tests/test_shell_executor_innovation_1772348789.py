import pytest
from neural_engine.shell_executor import ShellExecutor

def test_shell_executor_happy_path():
    executor = ShellExecutor(["ls", "echo"])
    assert executor.allowed_commands == ["ls", "echo"]

def test_shell_executor_empty_list():
    executor = ShellExecutor([])
    assert executor.allowed_commands == ["ls", "echo", "pwd", "whoami", "date"]

def test_shell_executor_none_input():
    executor = ShellExecutor(None)
    assert executor.allowed_commands == ["ls", "echo", "pwd", "whoami", "date"]

def test_shell_executor_boundary_values():
    executor = ShellExecutor(["ls", "echo", "pwd", "whoami", "date"])
    assert executor.allowed_commands == ["ls", "echo", "pwd", "whoami", "date"]

# Error cases are not applicable as the function does not raise exceptions