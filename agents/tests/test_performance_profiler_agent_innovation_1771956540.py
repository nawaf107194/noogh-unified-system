import pytest

from agents.performance_profiler_agent import PerformanceProfilerAgent, AgentRole

def test_init_happy_path():
    agent = PerformanceProfilerAgent()
    assert isinstance(agent.role, AgentRole)
    assert agent.role.name == "performance_profiler"
    assert hasattr(agent, "_profile_code")
    assert hasattr(agent, "_identify_bottlenecks")

def test_init_empty_role_name():
    with pytest.raises(TypeError):
        class EmptyRole:
            pass
        role = EmptyRole()
        PerformanceProfilerAgent(role=role)

def test_init_none_role_name():
    with pytest.raises(TypeError):
        role = None
        PerformanceProfilerAgent(role=role)

def test_init_invalid_role_type():
    with pytest.raises(TypeError):
        role = "invalid_role"
        PerformanceProfilerAgent(role=role)