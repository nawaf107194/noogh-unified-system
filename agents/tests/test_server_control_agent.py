import pytest
from pathlib import Path
import subprocess

class MockServerControlAgent:
    def get_process_status(self, name: str, config: Dict) -> Dict:
        return super().get_process_status(name, config)

@pytest.fixture
def agent():
    return MockServerControlAgent()

def test_happy_path(agent):
    pid_file = "path/to/existing.pid"
    with open(pid_file, 'w') as f:
        f.write("1234")
    
    config = {
        "pid_file": pid_file,
        "desc": "test_process"
    }
    
    result = agent.get_process_status("process_name", config)
    assert result == {
        "name": "process_name",
        "pid": 1234,
        "cpu": 0.0,  # Assuming no CPU usage in this mock
        "mem_pct": 0.0,  # Assuming no memory usage in this mock
        "uptime": "?",  # Assuming no uptime info in this mock
        "ok": True,
        "desc": "test_process"
    }

def test_empty_config(agent):
    result = agent.get_process_status("process_name", {})
    assert result == {
        "name": "process_name",
        "pid": None,
        "ok": False,
        "desc": ""
    }

def test_none_pid_file(agent):
    config = {
        "pid_file": None,
        "desc": "test_process"
    }
    
    result = agent.get_process_status("process_name", config)
    assert result == {
        "name": "process_name",
        "pid": None,
        "ok": False,
        "desc": "test_process"
    }

def test_invalid_pid_file(agent):
    pid_file = "path/to/invalid.pid"
    with open(pid_file, 'w') as f:
        f.write("abc")
    
    config = {
        "pid_file": pid_file,
        "desc": "test_process"
    }
    
    result = agent.get_process_status("process_name", config)
    assert result == {
        "name": "process_name",
        "pid": None,
        "ok": False,
        "desc": "test_process"
    }

def test_no_pid_file(agent):
    pid_file = "path/to/non_existent.pid"
    
    config = {
        "pid_file": pid_file,
        "desc": "test_process"
    }
    
    result = agent.get_process_status("process_name", config)
    assert result == {
        "name": "process_name",
        "pid": None,
        "ok": False,
        "desc": "test_process"
    }

def test_invalid_pid(agent):
    pid_file = "path/to/invalid_pid.pid"
    with open(pid_file, 'w') as f:
        f.write("-1")
    
    config = {
        "pid_file": pid_file,
        "desc": "test_process"
    }
    
    result = agent.get_process_status("process_name", config)
    assert result == {
        "name": "process_name",
        "pid": None,
        "ok": False,
        "desc": "test_process"
    }

def test_command_failure(agent, monkeypatch):
    pid_file = "path/to/existing.pid"
    with open(pid_file, 'w') as f:
        f.write("1234")
    
    config = {
        "pid_file": pid_file,
        "desc": "test_process"
    }
    
    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: subprocess.CompletedProcess(args, returncode=1))
    
    result = agent.get_process_status("process_name", config)
    assert result == {
        "name": "process_name",
        "pid": None,
        "ok": False,
        "desc": "test_process"
    }

def test_command_timeout(agent, monkeypatch):
    pid_file = "path/to/existing.pid"
    with open(pid_file, 'w') as f:
        f.write("1234")
    
    config = {
        "pid_file": pid_file,
        "desc": "test_process"
    }
    
    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: subprocess.CompletedProcess(args, returncode=0, stdout=""))
    
    result = agent.get_process_status("process_name", config)
    assert result == {
        "name": "process_name",
        "pid": None,
        "ok": False,
        "desc": "test_process"
    }