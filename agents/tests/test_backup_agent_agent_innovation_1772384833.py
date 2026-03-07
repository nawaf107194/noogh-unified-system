import pytest
from unittest.mock import patch, MagicMock

from agents.backup_agent_agent import BackupAgentAgent

class TestBackupAgentAgent:
    @patch('agents.backup_agent_agent.AgentRole')
    def test_backup_agent_agent_init_happy_path(self, mock_role):
        # Arrange
        role = mock_role.return_value
        
        # Act
        agent = BackupAgentAgent()
        
        # Assert
        mock_role.assert_called_once_with("backup_agent")
        assert agent.role == role
        assert agent.handlers == {
            "CREATE_BACKUP": agent._create_backup,
            "VERIFY_BACKUP": agent._verify_backup,
        }
        logger.info.assert_called_once_with("✅ BackupAgentAgent initialized")

    @patch('agents.backup_agent_agent.AgentRole')
    def test_backup_agent_agent_init_empty_role(self, mock_role):
        # Arrange
        role = None
        
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            BackupAgentAgent(role)
        
        assert "role" in str(exc_info.value)

    @patch('agents.backup_agent_agent.AgentRole')
    def test_backup_agent_agent_init_invalid_handler(self, mock_role):
        # Arrange
        custom_handlers = {
            "CREATE_BACKUP": None,
            "VERIFY_BACKUP": self._verify_backup,
        }
        
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            BackupAgentAgent(custom_handlers=custom_handlers)
        
        assert "handlers" in str(exc_info.value)

    @patch('agents.backup_agent_agent.AgentRole')
    def test_backup_agent_agent_init_boundary_handler(self, mock_role):
        # Arrange
        custom_handlers = {
            "CREATE_BACKUP": lambda: None,
            "VERIFY_BACKUP": self._verify_backup,
        }
        
        # Act
        agent = BackupAgentAgent(custom_handlers=custom_handlers)
        
        # Assert
        assert agent.handlers["CREATE_BACKUP"].__name__ == "<lambda>"

    @patch('agents.backup_agent_agent.AgentRole')
    def test_backup_agent_agent_init_boundary_custom_handler_name(self, mock_role):
        # Arrange
        custom_handlers = {
            "CREATE_BACKUP": self._create_backup,
            "VERIFY_BACKUP": lambda: None,
        }
        
        # Act
        agent = BackupAgentAgent(custom_handlers=custom_handlers)
        
        # Assert
        assert agent.handlers["VERIFY_BACKUP"].__name__ == "<lambda>"