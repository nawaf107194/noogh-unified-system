import pytest
from unittest.mock import patch, mock_open
from agents.log_analyzer_agent import LogAnalyzerAgent

class TestLogAnalyzerAgent:

    @pytest.fixture
    def agent(self):
        with patch('agents.log_analyzer_agent.logger') as mock_logger:
            yield LogAnalyzerAgent()

    def test_init_happy_path(self, agent):
        assert isinstance(agent.role, AgentRole)
        assert "ANALYZE_LOGS" in agent.custom_handlers
        assert "DETECT_ERROR_PATTERNS" in agent.custom_handlers
        assert "✅ LogAnalyzerAgent initialized" in agent.log_capture.getvalue()

    def test_init_custom_handlers_none(self, agent):
        with patch('agents.log_analyzer_agent.Agent.__init__') as mock_super:
            custom_handlers = None
            role = AgentRole("log_analyzer")
            LogAnalyzerAgent(role=role, custom_handlers=custom_handlers)
            assert "ANALYZE_LOGS" in mock_super.call_args[1]['custom_handlers']
            assert "DETECT_ERROR_PATTERNS" in mock_super.call_args[1]['custom_handlers']

    def test_init_role_none(self):
        with pytest.raises(ValueError) as exc_info:
            LogAnalyzerAgent(role=None)
        assert str(exc_info.value) == 'Agent role must be provided'

    @patch('agents.log_analyzer_agent.AgentRole')
    def test_init_role_invalid_type(self, mock_AgentRole, agent):
        with pytest.raises(TypeError) as exc_info:
            LogAnalyzerAgent(role="invalid")
        assert str(exc_info.value) == "role must be an instance of AgentRole"

    def test_init_log_capture(self, agent):
        assert "LogAnalyzerAgent initialized" in agent.log_capture.getvalue()

    @patch('agents.log_analyzer_agent.AgentRole')
    def test_init_with_custom_handlers_empty(self, mock_AgentRole, agent):
        with patch('agents.log_analyzer_agent.Agent.__init__') as mock_super:
            custom_handlers = {}
            role = AgentRole("log_analyzer")
            LogAnalyzerAgent(role=role, custom_handlers=custom_handlers)
            assert "ANALYZE_LOGS" not in mock_super.call_args[1]['custom_handlers']
            assert "DETECT_ERROR_PATTERNS" not in mock_super.call_args[1]['custom_handlers']

    @patch('agents.log_analyzer_agent.AgentRole')
    def test_init_with_custom_handlers_invalid(self, mock_AgentRole, agent):
        with pytest.raises(KeyError) as exc_info:
            LogAnalyzerAgent(role=AgentRole("log_analyzer"), custom_handlers={"INVALID_KEY": "some_function"})
        assert str(exc_info.value) == "Invalid handler key: INVALID_KEY"