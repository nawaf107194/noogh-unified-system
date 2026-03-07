import pytest

from agents.backup_agent_agent import BackupAgentAgent, AgentRole

class TestBackupAgentAgent:

    def test_happy_path(self):
        agent = BackupAgentAgent()
        assert hasattr(agent, "_create_backup")
        assert hasattr(agent, "_verify_backup")
        assert isinstance(agent.role, AgentRole)
        assert agent.role.name == "backup_agent"
        assert len(agent.custom_handlers) == 2
        assert "CREATE_BACKUP" in agent.custom_handlers
        assert "VERIFY_BACKUP" in agent.custom_handlers
        assert callable(agent.custom_handlers["CREATE_BACKUP"])
        assert callable(agent.custom_handlers["VERIFY_BACKUP"])
        logger_mock = pytest.mock.patch.object(BackupAgentAgent, 'logger')
        assert logger_mock.info.call_count == 1
        assert logger_mock.info.call_args[0][0] == "✅ BackupAgentAgent initialized"

    def test_edge_case_role_none(self):
        with pytest.raises(ValueError):
            agent = BackupAgentAgent(role=None)

    def test_error_case_invalid_handler_name(self):
        custom_handlers = {
            "CREATE_BACKUP": lambda: None,
            "INVALID_HANDLER": lambda: None,
        }
        with pytest.raises(TypeError):
            agent = BackupAgentAgent(custom_handlers=custom_handlers)