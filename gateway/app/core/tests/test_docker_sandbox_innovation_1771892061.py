import pytest

from gateway.app.core.docker_sandbox import get_local_sandbox, LocalDockerSandbox

@pytest.fixture(autouse=True)
def reset_sandbox():
    global _sandbox
    _sandbox = None

def test_get_local_sandbox_happy_path(monkeypatch):
    mock_sandbox = LocalDockerSandbox()
    monkeypatch.setattr('gateway.app.core.docker_sandbox.LocalDockerSandbox', lambda: mock_sandbox)
    
    result = get_local_sandbox()
    assert result == mock_sandbox

def test_get_local_sandbox_first_call():
    result = get_local_sandbox()
    assert isinstance(result, LocalDockerSandbox)

def test_get_local_sandbox_subsequent_calls_same_instance(monkeypatch):
    first_result = get_local_sandbox()
    monkeypatch.setattr('gateway.app.core.docker_sandbox.LocalDockerSandbox', lambda: None)
    second_result = get_local_sandbox()
    
    assert first_result == second_result
    assert isinstance(first_result, LocalDockerSandbox)

def test_get_local_sandbox_no_mock():
    result = get_local_sandbox()
    assert isinstance(result, LocalDockerSandbox)