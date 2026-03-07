import pytest
from unittest.mock import patch, Mock, MagicMock
from docker.errors import APIError

from sandbox_service.app.core.sandbox_impl import SandboxImpl

@pytest.fixture
def sandbox_instance():
    return SandboxImpl(
        client=MagicMock(),
        image="test_image",
        mem_limit="128m",
        cpu_quota=50,
        workdir="/workdir"
    )

@patch('sandbox_service.app.core.sandbox_impl.time.time')
def test_execute_code_happy_path(mock_time, sandbox_instance):
    mock_time.return_value = 0
    sandbox_instance.client.containers.run.return_value = MagicMock()
    
    result = sandbox_instance.execute_code("print('Hello')", "python")
    
    assert result == {
        "success": True,
        "output": "total 4\n-rw-r--r-- 1 user group 5 Jan  1 00:00 script.py",
        "error": None,
        "exit_code": 0,
        "duration_ms": 0
    }
    
@patch('sandbox_service.app.core.sandbox_impl.time.time')
def test_execute_code_empty_input(mock_time, sandbox_instance):
    mock_time.return_value = 0
    sandbox_instance.client.containers.run.return_value = MagicMock()
    
    result = sandbox_instance.execute_code("")
    
    assert result == {
        "success": False,
        "output": "",
        "error": "Sandbox file missing. LS output: total 0",
        "exit_code": 1,
        "duration_ms": 0
    }

@patch('sandbox_service.app.core.sandbox_impl.time.time')
def test_execute_code_invalid_user(mock_time, sandbox_instance):
    mock_time.return_value = 0
    sandbox_instance.client.containers.run.side_effect = APIError("linux spec user not found")
    
    with pytest.raises(RuntimeError) as e:
        sandbox_instance.execute_code("print('Hello')")
    
    assert str(e.value) == "Sandbox Security Failure: Invalid User Configuration"

@patch('sandbox_service.app.core.sandbox_impl.time.time')
def test_execute_code_timeout(mock_time, sandbox_instance):
    mock_time.return_value = 0
    sandbox_instance.client.containers.run.return_value.exec_run.side_effect = APIError("timeout expired")
    
    result = sandbox_instance.execute_code("sleep 5", timeout=1)
    
    assert result == {
        "success": False,
        "output": "",
        "error": f"Execution timed out after {1}s",
        "exit_code": 124,
        "duration_ms": 0
    }

@patch('sandbox_service.app.core.sandbox_impl.time.time')
def test_execute_code_general_exception(mock_time, sandbox_instance):
    mock_time.return_value = 0
    sandbox_instance.client.containers.run.side_effect = Exception("General Error")
    
    result = sandbox_instance.execute_code("print('Hello')")
    
    assert result == {
        "success": False,
        "output": "",
        "error": "General Error",
        "exit_code": -1,
        "duration_ms": 0
    }