import pytest
from unittest.mock import patch, MagicMock

from agents.dependency_auditor_agent import DependencyAuditorAgent, AgentRole

class MockLogger:
    def info(self, message):
        pass

@pytest.fixture
def mock_logger():
    return MockLogger()

@patch('agents.dependency_auditor_agent.logger', new_callable=MockLogger)
def test_dependency_auditor_agent_init_happy_path(mock_logger):
    agent = DependencyAuditorAgent()
    assert isinstance(agent.role, AgentRole)
    assert agent.role.name == "dependency_auditor"
    assert "AUDIT_DEPS" in agent._custom_handlers
    assert "CHECK_VULNERABILITIES" in agent._custom_handlers
    mock_logger.info.assert_called_once_with("✅ DependencyAuditorAgent initialized")

@patch('agents.dependency_auditor_agent.AgentRole')
def test_dependency_auditor_agent_init_edge_case_empty_role(mock_AgentRole):
    with pytest.raises(ValueError):
        mock_AgentRole.side_effect = ValueError("Invalid role name")
        agent = DependencyAuditorAgent()

@patch('agents.dependency_auditor_agent.logger', new_callable=MockLogger)
def test_dependency_auditor_agent_init_error_case_invalid_custom_handler(mock_logger):
    custom_handlers = {
        "AUDIT_DEPS": None,
        "CHECK_VULNERABILITIES": lambda: True,
    }
    with pytest.raises(TypeError):
        agent = DependencyAuditorAgent(custom_handlers=custom_handlers)

@patch('agents.dependency_auditor_agent.logger', new_callable=MockLogger)
def test_dependency_auditor_agent_init_async_behavior(mock_logger):
    class MockAsyncAgent(DependencyAuditorAgent):
        async def _audit_dependencies(self):
            return {"deps": []}
        
        async def _check_vulnerabilities(self):
            return {"vulnerabilities": []}

    agent = MockAsyncAgent()
    assert isinstance(agent.role, AgentRole)
    assert agent.role.name == "dependency_auditor"
    assert "AUDIT_DEPS" in agent._custom_handlers
    assert "CHECK_VULNERABILITIES" in agent._custom_handlers
    mock_logger.info.assert_called_once_with("✅ DependencyAuditorAgent initialized")