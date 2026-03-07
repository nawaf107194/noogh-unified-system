import pytest
from unittest.mock import Mock, patch
from agents.code_executor_agent import CodeExecutorAgent, AgentRole

class TestCodeExecutorAgent:

    @pytest.fixture
    def agent(self):
        return CodeExecutorAgent()

    @patch('agents.code_executor_agent.logger.info')
    def test_init_happy_path(self, mock_logger_info, agent):
        assert isinstance(agent, CodeExecutorAgent)
        assert agent.role == AgentRole.CODE_EXECUTOR
        assert agent.custom_handlers == {
            "ANALYZE_CODE": agent._analyze_code,
            "GENERATE_CODE_PATCHES": agent._generate_patches,
            "DETECT_MALICIOUS_CODE": agent._detect_malicious,
        }
        mock_logger_info.assert_called_once_with("✅ CodeExecutorAgent initialized")

    def test_init_edge_case_none(self):
        with pytest.raises(TypeError) as excinfo:
            custom_handlers = None
            super().__init__(AgentRole.CODE_EXECUTOR, custom_handlers)
        assert "custom_handlers cannot be None" in str(excinfo.value)

    @patch('agents.code_executor_agent.logger.info')
    def test_init_edge_case_empty(self, mock_logger_info):
        with pytest.raises(ValueError) as excinfo:
            custom_handlers = {}
            super().__init__(AgentRole.CODE_EXECUTOR, custom_handlers)
        assert "custom_handlers cannot be empty" in str(excinfo.value)

    @patch('agents.code_executor_agent.logger.info')
    def test_init_error_case_invalid_handler(self, mock_logger_info):
        with pytest.raises(ValueError) as excinfo:
            custom_handlers = {
                "ANALYZE_CODE": self._analyze_code,
                "INVALID_HANDLER": self._generate_patches,
            }
            super().__init__(AgentRole.CODE_EXECUTOR, custom_handlers)
        assert "Invalid handler in custom_handlers" in str(excinfo.value)

    @patch('agents.code_executor_agent.logger.info')
    def test_init_error_case_missing_handler(self, mock_logger_info):
        with pytest.raises(ValueError) as excinfo:
            custom_handlers = {
                "ANALYZE_CODE": self._analyze_code,
            }
            super().__init__(AgentRole.CODE_EXECUTOR, custom_handlers)
        assert "Missing handler in custom_handlers" in str(excinfo.value)

    # Async behavior tests (if applicable)
    @patch('agents.code_executor_agent.logger.info')
    async def test_init_async_behavior(self, mock_logger_info):
        agent = CodeExecutorAgent()
        await asyncio.sleep(0)  # Simulate an asynchronous operation
        assert isinstance(agent, CodeExecutorAgent)
        assert agent.role == AgentRole.CODE_EXECUTOR
        assert agent.custom_handlers == {
            "ANALYZE_CODE": agent._analyze_code,
            "GENERATE_CODE_PATCHES": agent._generate_patches,
            "DETECT_MALICIOUS_CODE": agent._detect_malicious,
        }
        mock_logger_info.assert_called_once_with("✅ CodeExecutorAgent initialized")