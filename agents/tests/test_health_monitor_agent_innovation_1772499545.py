import pytest

from agents.health_monitor_agent import HealthMonitorAgent, AgentRole, logger

class MockLogger:
    @staticmethod
    def info(message):
        pass

logger.info = MockLogger.info

def test_init_happy_path():
    agent = HealthMonitorAgent()
    assert isinstance(agent.role, AgentRole)
    assert agent.role.name == "health_monitor"
    assert hasattr(agent, "_monitor_health")
    assert hasattr(agent, "_check_services")

def test_init_empty_custom_handlers():
    custom_handlers = {}
    with pytest.raises(ValueError):
        role = AgentRole("health_monitor")
        HealthMonitorAgent(role, custom_handlers)

def test_init_none_custom_handlers():
    custom_handlers = None
    with pytest.raises(ValueError):
        role = AgentRole("health_monitor")
        HealthMonitorAgent(role, custom_handlers)

def test_init_invalid_role_type():
    role = "invalid_role"
    with pytest.raises(TypeError):
        HealthMonitorAgent(role)