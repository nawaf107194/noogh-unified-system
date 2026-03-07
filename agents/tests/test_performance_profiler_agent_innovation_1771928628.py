import pytest
from unittest.mock import patch, MagicMock

from agents.performance_profiler_agent import PerformanceProfilerAgent, AgentRole

class MockLogger:
    def info(self, message):
        pass

@pytest.fixture
def profiler_agent():
    return PerformanceProfilerAgent()

def test_init_happy_path(profiler_agent):
    assert profiler_agent.role.name == "performance_profiler"
    assert profiler_agent.handlers["PROFILE_CODE"] is profiler_agent._profile_code
    assert profiler_agent.handlers["IDENTIFY_BOTTLENECKS"] is profiler_agent._identify_bottlenecks

def test_init_custom_logger(profiler_agent):
    with patch.object(PerformanceProfilerAgent, 'logger', new=MagicMock(spec=MockLogger)):
        profiler_agent = PerformanceProfilerAgent()
        profiler_agent.logger.info.assert_called_once_with("✅ PerformanceProfilerAgent initialized")

def test_init_role_none():
    role = None
    agent = PerformanceProfilerAgent(role)
    assert agent.role is not None
    assert agent.role.name == "performance_profiler"

def test_init_handlers_empty(profiler_agent):
    custom_handlers = {}
    with patch.object(PerformanceProfilerAgent, 'custom_handlers', new=MagicMock(return_value=custom_handlers)):
        profiler_agent = PerformanceProfilerAgent()
        assert profiler_agent.handlers == {}

def test_init_custom_handler_none():
    custom_handlers = {
        "PROFILE_CODE": None,
        "IDENTIFY_BOTTLENECKS": profiler_agent._identify_bottlenecks
    }
    with patch.object(PerformanceProfilerAgent, 'custom_handlers', new=MagicMock(return_value=custom_handlers)):
        profiler_agent = PerformanceProfilerAgent()
        assert profiler_agent.handlers["PROFILE_CODE"] is None
        assert profiler_agent.handlers["IDENTIFY_BOTTLENECKS"] is profiler_agent._identify_bottlenecks

def test_init_custom_handler_not_callable(profiler_agent):
    custom_handlers = {
        "PROFILE_CODE": 123,
        "IDENTIFY_BOTTLENECKS": profiler_agent._identify_bottlenecks
    }
    with patch.object(PerformanceProfilerAgent, 'custom_handlers', new=MagicMock(return_value=custom_handlers)):
        profiler_agent = PerformanceProfilerAgent()
        assert profiler_agent.handlers["PROFILE_CODE"] is None
        assert profiler_agent.handlers["IDENTIFY_BOTTLENECKS"] is profiler_agent._identify_bottlenecks

def test_init_logger_error(profiler_agent):
    with patch.object(PerformanceProfilerAgent, 'logger', new=MagicMock(spec=MockLogger)):
        profiler_agent.logger.info.side_effect = Exception("Test Error")
        profiler_agent = PerformanceProfilerAgent()
        # No assertion needed here as we're not checking for exceptions raised by the logger

def test_init_role_invalid_type(profiler_agent):
    role = "invalid_role"
    with pytest.raises(TypeError):
        PerformanceProfilerAgent(role)

def test_init_handlers_invalid_type(profiler_agent):
    custom_handlers = {
        "PROFILE_CODE": 123,
        "IDENTIFY_BOTTLENECKS": profiler_agent._identify_bottlenecks
    }
    with pytest.raises(TypeError):
        PerformanceProfilerAgent(custom_handlers=custom_handlers)