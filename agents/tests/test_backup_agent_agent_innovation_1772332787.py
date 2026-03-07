import pytest

from agents.backup_agent_agent import BackupAgentAgent, AgentRole, logger

class TestBackupAgentAgent:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.agent = BackupAgentAgent()

    def test_happy_path(self):
        assert isinstance(self.agent.role, AgentRole)
        assert self.agent.role.name == "backup_agent"
        assert hasattr(self.agent.handlers, "CREATE_BACKUP")
        assert hasattr(self.agent.handlers, "VERIFY_BACKUP")

    def test_edge_case_no_custom_handlers(self):
        with pytest.raises(ValueError, match="custom_handlers cannot be empty"):
            BackupAgentAgent(custom_handlers={})

    def test_async_behavior(self, monkeypatch):
        async def mock_create_backup(*args, **kwargs):
            return True

        async def mock_verify_backup(*args, **kwargs):
            return True

        monkeypatch.setattr(BackupAgentAgent, "_create_backup", mock_create_backup)
        monkeypatch.setattr(BackupAgentAgent, "_verify_backup", mock_verify_backup)

        result = self.agent.handle_request("CREATE_BACKUP")
        assert result is True

        result = self.agent.handle_request("VERIFY_BACKUP")
        assert result is True