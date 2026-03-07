import pytest
from gateway.app.core.agent_kernel import AgentKernel

@pytest.fixture
def agent_kernel():
    return AgentKernel(max_steps=10, max_time_ms=500)

def test_is_exhausted_happy_path(agent_kernel):
    assert not agent_kernel.is_exhausted()[0], "Should not be exhausted"
    agent_kernel.used_steps = 9
    assert agent_kernel.is_exhausted()[0], "Should be exhausted due to steps limit"
    agent_kernel.used_steps = 10
    agent_kernel.max_time_ms = 450
    assert agent_kernel.is_exhausted()[0], "Should be exhausted due to time limit"

def test_is_exhausted_edge_cases(agent_kernel):
    agent_kernel._start = None
    assert not agent_kernel.is_exhausted()[0], "Should not be exhausted with _start as None"
    agent_kernel._start = 1633072800.0  # Example timestamp in seconds
    agent_kernel.used_steps = 11
    agent_kernel.max_time_ms = -500
    assert not agent_kernel.is_exhausted()[0], "Should not be exhausted with negative time limit"

def test_is_exhausted_error_cases():
    with pytest.raises(TypeError):
        AgentKernel(max_steps="invalid", max_time_ms=500)
    with pytest.raises(TypeError):
        AgentKernel(max_steps=10, max_time_ms="invalid")

# Async behavior (not applicable as the function is synchronous)