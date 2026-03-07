import pytest
from neural_engine.shell_executor import ShellExecutor

@pytest.fixture
def shell_executor():
    return ShellExecutor(allowed_commands=['ls', 'echo'])

def test_happy_path(shell_executor):
    result = shell_executor.execute('echo Hello, World!')
    assert "Hello, World!" in result, f"Expected output not found: {result}"

def test_empty_command(shell_executor):
    result = shell_executor.execute('')
    assert result == "Empty command.", f"Unexpected result for empty command: {result}"

def test_none_command(shell_executor):
    result = shell_executor.execute(None)
    assert result == "Empty command.", f"Unexpected result for None command: {result}"

def test_denied_command(shell_executor):
    result = shell_executor.execute('rm -rf /')
    assert "Command denied" in result, f"Expected denial message not found: {result}"

def test_timeout(shell_executor, monkeypatch):
    import time
    from unittest.mock import patch

    with patch.object(subprocess, 'run') as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=5)
        result = shell_executor.execute('sleep 10')
        assert "Execution timed out" in result, f"Expected timeout message not found: {result}"

def test_general_failure(shell_executor, monkeypatch):
    import time
    from unittest.mock import patch

    with patch.object(subprocess, 'run') as mock_run:
        mock_run.side_effect = Exception('General error')
        result = shell_executor.execute('some_command')
        assert "Execution failed" in result, f"Expected failure message not found: {result}"