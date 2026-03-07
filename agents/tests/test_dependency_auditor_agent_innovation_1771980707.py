import pytest

from agents.dependency_auditor_agent import DependencyAuditorAgent, AgentRole, logger

class MockAgentSuperClass:
    def __init__(self, role, custom_handlers):
        self.role = role
        self.custom_handlers = custom_handlers

# Patch the super class to use the mock
DependencyAuditorAgent.super_class = MockAgentSuperClass

@pytest.fixture
def dependency_auditor_agent():
    return DependencyAuditorAgent()

def test_init_happy_path(dependency_auditor_agent):
    assert dependency_auditor_agent.role.name == "dependency_auditor"
    assert "AUDIT_DEPS" in dependency_auditor_agent.custom_handlers
    assert "CHECK_VULNERABILITIES" in dependency_auditor_agent.custom_handlers

def test_init_logger_message(capsys, dependency_auditor_agent):
    captured = capsys.readouterr()
    assert "✅ DependencyAuditorAgent initialized" in captured.out

def test_init_no_custom_handlers():
    agent = DependencyAuditorAgent(custom_handlers={})
    assert agent.role.name == "dependency_auditor"
    assert not agent.custom_handlers

def test_init_invalid_role_type():
    with pytest.raises(TypeError):
        AgentRole(123)

def test_init_custom_handler_not_callable():
    with pytest.raises(ValueError):
        custom_handlers = {
            "AUDIT_DEPS": 123,
            "CHECK_VULNERABILITIES": dependency_auditor_agent._check_vulnerabilities,
        }
        DependencyAuditorAgent(custom_handlers=custom_handlers)