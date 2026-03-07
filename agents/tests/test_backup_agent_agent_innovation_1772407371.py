import pytest
from agents.backup_agent_agent import BackupAgentAgent, AgentRole

class TestBackupAgentAgent:

    @pytest.fixture
    def backup_agent_agent(self):
        return BackupAgentAgent()

    def test_init_happy_path(self, backup_agent_agent):
        assert isinstance(backup_agent_agent.role, AgentRole)
        assert backup_agent_agent.role.name == "backup_agent"
        assert "CREATE_BACKUP" in backup_agent_agent.custom_handlers
        assert backup_agent_agent.custom_handlers["CREATE_BACKUP"] is backup_agent_agent._create_backup
        assert "VERIFY_BACKUP" in backup_agent_agent.custom_handlers
        assert backup_agent_agent.custom_handlers["VERIFY_BACKUP"] is backup_agent_agent._verify_backup

    def test_init_edge_case_no_custom_handlers(self, backup_agent_agent):
        role = AgentRole("backup_agent")
        agent = BackupAgentAgent(role)
        assert "CREATE_BACKUP" not in agent.custom_handlers
        assert "VERIFY_BACKUP" not in agent.custom_handlers

    def test_init_edge_case_empty_role_name(self, backup_agent_agent):
        role = AgentRole("")
        with pytest.raises(ValueError) as exc_info:
            BackupAgentAgent(role)
        assert str(exc_info.value) == "Role name cannot be empty"

    def test_init_error_case_none_role(self):
        with pytest.raises(TypeError) as exc_info:
            BackupAgentAgent(None)
        assert str(exc_info.value) == "role must be an instance of AgentRole"