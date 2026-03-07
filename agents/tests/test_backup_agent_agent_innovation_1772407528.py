import pytest

from agents.backup_agent_agent import BackupAgentAgent, AgentRole, logger

class MockLogger:
    @staticmethod
    def info(message):
        pass

logger.info = MockLogger.info

def test_init_happy_path():
    agent = BackupAgentAgent()
    assert hasattr(agent, "custom_handlers")
    assert agent.custom_handlers == {
        "CREATE_BACKUP": agent._create_backup,
        "VERIFY_BACKUP": agent._verify_backup,
    }
    assert isinstance(agent.role, AgentRole)
    assert agent.role.name == "backup_agent"
    assert logger.info.call_count == 1

def test_init_empty_custom_handlers():
    with pytest.raises(TypeError):
        BackupAgentAgent(custom_handlers={})

def test_init_none_role():
    with pytest.raises(TypeError):
        BackupAgentAgent(role=None)

def test_init_invalid_custom_handler_key():
    custom_handlers = {
        "CREATE_BACKUP": None,
        "VERIFY_BACKUP": None,
    }
    agent = BackupAgentAgent(custom_handlers=custom_handlers)
    assert hasattr(agent, "custom_handlers")
    assert agent.custom_handlers == {
        "CREATE_BACKUP": None,
        "VERIFY_BACKUP": None,
    }
    assert isinstance(agent.role, AgentRole)
    assert agent.role.name == "backup_agent"