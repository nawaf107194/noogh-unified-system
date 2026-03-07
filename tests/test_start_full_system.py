import pytest
from unittest.mock import patch, MagicMock
import subprocess

class MockSystem:
    def __init__(self):
        self.processes = {}
    
    def success(self, message):
        print(message)

@pytest.fixture
def mock_system():
    return MockSystem()

@pytest.mark.parametrize("cmd, name, background", [
    (["echo", "test"], "Test Process", True),  # Normal case
    (["ls", "-l"], "List Files", False),       # Normal case without background
])
def test_run_cmd_happy_path(mock_system, cmd, name, background):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.pid = 12345
        result = mock_system.run_cmd(cmd, name, background)
        assert result == mock_popen.return_value
        if background:
            assert name in mock_system.processes
            assert mock_system.processes[name] == mock_popen.return_value
        else:
            assert mock_system.processes.get(name) is None

@pytest.mark.parametrize("cmd, name, background", [
    ([], "Empty Command", True),  # Empty command list
    (None, "Null Command", True), # Null command
    (["echo", "test"], "", True), # Empty name
    (["echo", "test"], None, True), # Null name
])
def test_run_cmd_edge_cases(mock_system, cmd, name, background):
    with patch("subprocess.Popen") as mock_popen:
        if cmd and name:
            mock_system.run_cmd(cmd, name, background)
            mock_popen.assert_called_once()
        else:
            with pytest.raises(Exception):  # Adjust based on expected exception type
                mock_system.run_cmd(cmd, name, background)

@pytest.mark.parametrize("cmd, name, background", [
    (["nonexistentcommand"], "Invalid Command", True),  # Invalid command
    (["echo", "test"], "Invalid Directory", True, "/nonexistent/directory"),  # Invalid directory
])
def test_run_cmd_error_cases(mock_system, cmd, name, background):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.side_effect = subprocess.CalledProcessError(returncode=1, cmd=cmd)
        with pytest.raises(subprocess.CalledProcessError):
            mock_system.run_cmd(cmd, name, background)

def test_run_cmd_async_behavior(mock_system):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.pid = 12345
        proc = mock_system.run_cmd(["echo", "test"], "Async Test", True)
        assert proc.poll() is None  # Check if the process is still running