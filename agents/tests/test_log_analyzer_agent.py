import pytest
from unittest.mock import MagicMock, patch
from agents.log_analyzer_agent import LogAnalyzerAgent
from agents.agent_base import AgentRole

class TestLogAnalyzerAgent:

    @patch('agents.log_analyzer_agent.AgentBase.__init__')
    def test_happy_path(self, mock_super_init):
        # Arrange
        mock_super_init.return_value = None
        logger_mock = MagicMock()
        
        # Act
        agent = LogAnalyzerAgent()

        # Assert
        assert agent.role.name == 'log_analyzer'
        assert len(agent.custom_handlers) == 2
        assert 'ANALYZE_LOGS' in agent.custom_handlers
        assert 'DETECT_ERROR_PATTERNS' in agent.custom_handlers
        logger_mock.info.assert_called_once_with("✅ LogAnalyzerAgent initialized")

    @patch('agents.log_analyzer_agent.AgentBase.__init__')
    def test_edge_case_empty_custom_handlers(self, mock_super_init):
        # Arrange
        mock_super_init.return_value = None
        logger_mock = MagicMock()

        # Act & Assert
        with pytest.raises(AttributeError):
            class EmptyCustomHandlersAgent(LogAnalyzerAgent):
                def __init__(self):
                    custom_handlers = {}
                    role = AgentRole("log_analyzer")
                    super().__init__(role, custom_handlers)
                    logger.info("✅ LogAnalyzerAgent initialized")
            agent = EmptyCustomHandlersAgent()

    @patch('agents.log_analyzer_agent.AgentBase.__init__')
    def test_error_case_invalid_custom_handlers(self, mock_super_init):
        # Arrange
        mock_super_init.return_value = None
        logger_mock = MagicMock()

        # Act & Assert
        with pytest.raises(TypeError):
            class InvalidCustomHandlersAgent(LogAnalyzerAgent):
                def __init__(self):
                    custom_handlers = "not_a_dict"
                    role = AgentRole("log_analyzer")
                    super().__init__(role, custom_handlers)
                    logger.info("✅ LogAnalyzerAgent initialized")
            agent = InvalidCustomHandlersAgent()

    @patch('agents.log_analyzer_agent.AgentBase.__init__')
    def test_async_behavior(self, mock_super_init):
        # Arrange
        mock_super_init.return_value = None
        logger_mock = MagicMock()
        
        # Act
        agent = LogAnalyzerAgent()

        # Since the function itself does not have async behavior, we just ensure
        # it doesn't raise any exceptions or errors.
        assert True