import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess
import time

class MockServerControlAgent:
    def __init__(self):
        self.restart_process = MagicMock()

@pytest.fixture
def agent():
    return MockServerControlAgent()

@patch('subprocess.run')
@patch('time.sleep')
@patch('pathlib.Path.exists')
def test_restart_process_happy_path(mock_exists, mock_sleep, mock_run, agent):
    mock_exists.return_value = True
    mock_run.return_value = None

    config = {
        "pid_file": "/tmp/test.pid",
        "script": "test_script.py",
        "args": ["arg1", "arg2"]
    }
    
    result = agent.restart_process("test_name", config)
    
    assert result == True
    mock_exists.assert_called_once_with("/tmp/test.pid")
    mock_run.assert_called_once_with(["kill", "1234"], capture_output=True, timeout=5)
    mock_sleep.assert_called_once_with(2)
    mock_run.reset_mock()

    mock_exists.return_value = False

    result = agent.restart_process("test_name", config)
    
    assert result == True
    mock_exists.assert_called_once_with("/tmp/test.pid")
    mock_run.assert_not_called()
    mock_sleep.assert_not_called()

@patch('subprocess.run')
def test_restart_process_edge_cases(mock_run, agent):
    config = {
        "pid_file": "",
        "script": "",
        "args": []
    }
    
    result = agent.restart_process("test_name", config)
    
    assert result == True
    mock_run.assert_not_called()

@patch('subprocess.run')
def test_restart_process_error_cases(mock_run, agent):
    mock_run.side_effect = subprocess.CalledProcessError(1, "kill")
    
    config = {
        "pid_file": "/tmp/test.pid",
        "script": "test_script.py",
        "args": ["arg1", "arg2"]
    }
    
    result = agent.restart_process("test_name", config)
    
    assert result == False