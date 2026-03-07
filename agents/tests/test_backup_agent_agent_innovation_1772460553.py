import pytest

from agents.backup_agent_agent import BackupAgentAgent
from agents.agent_role import AgentRole
from unittest.mock import patch, MagicMock

class TestBackupAgentAgent:

    @patch('agents.backup_agent_agent.Agent')
    def test_happy_path(self, mock_agent):
        # Setup
        role = AgentRole("backup_agent")
        custom_handlers = {
            "CREATE_BACKUP": lambda: None,
            "VERIFY_BACKUP": lambda: None,
        }
        
        # Call the constructor
        backup_agent = BackupAgentAgent(role, custom_handlers)
        
        # Assertions
        mock_agent.assert_called_once_with(role, custom_handlers)
        assert isinstance(backup_agent, BackupAgentAgent)
        assert backup_agent.logger.info.call_args_list == [pytest.param("✅ BackupAgentAgent initialized",), pytest.param(None,)]

    @patch('agents.backup_agent_agent.Agent')
    def test_edge_case_empty_custom_handlers(self, mock_agent):
        # Setup
        role = AgentRole("backup_agent")
        custom_handlers = {}
        
        # Call the constructor
        backup_agent = BackupAgentAgent(role, custom_handlers)
        
        # Assertions
        mock_agent.assert_called_once_with(role, custom_handlers)
        assert isinstance(backup_agent, BackupAgentAgent)
        assert backup_agent.logger.info.call_args_list == [pytest.param("✅ BackupAgentAgent initialized",), pytest.param(None,)]

    @patch('agents.backup_agent_agent.Agent')
    def test_edge_case_none_custom_handlers(self, mock_agent):
        # Setup
        role = AgentRole("backup_agent")
        custom_handlers = None
        
        # Call the constructor
        backup_agent = BackupAgentAgent(role, custom_handlers)
        
        # Assertions
        mock_agent.assert_called_once_with(role, {})
        assert isinstance(backup_agent, BackupAgentAgent)
        assert backup_agent.logger.info.call_args_list == [pytest.param("✅ BackupAgentAgent initialized",), pytest.param(None,)]

    @patch('agents.backup_agent_agent.Agent')
    def test_error_case_invalid_role(self, mock_agent):
        # Setup
        role = None
        custom_handlers = {
            "CREATE_BACKUP": lambda: None,
            "VERIFY_BACKUP": lambda: None,
        }
        
        # Call the constructor and assert it raises an error
        with pytest.raises(ValueError) as exc_info:
            BackupAgentAgent(role, custom_handlers)
        
        # Assertions
        assert str(exc_info.value) == "Invalid role provided"
        mock_agent.assert_not_called()

    @patch('agents.backup_agent_agent.Agent')
    def test_error_case_invalid_custom_handler_key(self, mock_agent):
        # Setup
        role = AgentRole("backup_agent")
        custom_handlers = {
            "CREATE_BACKUP": lambda: None,
            "INVALID_KEY": lambda: None,
        }
        
        # Call the constructor and assert it raises an error
        with pytest.raises(ValueError) as exc_info:
            BackupAgentAgent(role, custom_handlers)
        
        # Assertions
        assert str(exc_info.value) == "Invalid handler key provided"
        mock_agent.assert_not_called()

    @patch('agents.backup_agent_agent.Agent')
    def test_error_case_empty_custom_handler_value(self, mock_agent):
        # Setup
        role = AgentRole("backup_agent")
        custom_handlers = {
            "CREATE_BACKUP": None,
            "VERIFY_BACKUP": lambda: None,
        }
        
        # Call the constructor and assert it raises an error
        with pytest.raises(ValueError) as exc_info:
            BackupAgentAgent(role, custom_handlers)
        
        # Assertions
        assert str(exc_info.value) == "Handler function cannot be None"
        mock_agent.assert_not_called()

    @patch('agents.backup_agent_agent.Agent')
    def test_error_case_none_custom_handler_value(self, mock_agent):
        # Setup
        role = AgentRole("backup_agent")
        custom_handlers = {
            "CREATE_BACKUP": None,
            "VERIFY_BACKUP": lambda: None,
        }
        
        # Call the constructor and assert it raises an error
        with pytest.raises(ValueError) as exc_info:
            BackupAgentAgent(role, custom_handlers)
        
        # Assertions
        assert str(exc_info.value) == "Handler function cannot be None"
        mock_agent.assert_not_called()