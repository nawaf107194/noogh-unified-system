import pytest
from agents.pipeline_optimizer_agent import PipelineOptimizerAgent, AgentRole
from unittest.mock import Mock

class TestPipelineOptimizerAgent:

    @pytest.fixture
    def agent(self):
        return PipelineOptimizerAgent()

    def test_happy_path(self, agent):
        assert isinstance(agent.role, AgentRole)
        assert "AUDIT_PIPELINE" in agent.handlers
        assert "OPTIMIZE_PIPELINE" in agent.handlers
        assert "ESTABLISH_PIPELINE_SECURITY" in agent.handlers

    def test_edge_case_empty_handler_dict(self):
        class MockAgent(PipelineOptimizerAgent):
            def __init__(self):
                custom_handlers = {}
                super().__init__(AgentRole.PIPELINE_OPTIMIZER, custom_handlers)
        
        mock_agent = MockAgent()
        assert isinstance(mock_agent.role, AgentRole)
        assert "AUDIT_PIPELINE" not in mock_agent.handlers
        assert "OPTIMIZE_PIPELINE" not in mock_agent.handlers
        assert "ESTABLISH_PIPELINE_SECURITY" not in mock_agent.handlers

    def test_edge_case_none_handler_dict(self):
        class MockAgent(PipelineOptimizerAgent):
            def __init__(self):
                custom_handlers = None
                super().__init__(AgentRole.PIPELINE_OPTIMIZER, custom_handlers)
        
        mock_agent = MockAgent()
        assert isinstance(mock_agent.role, AgentRole)
        assert "AUDIT_PIPELINE" not in mock_agent.handlers
        assert "OPTIMIZE_PIPELINE" not in mock_agent.handlers
        assert "ESTABLISH_PIPELINE_SECURITY" not in mock_agent.handlers

    def test_error_case_invalid_handler_type(self):
        class MockAgent(PipelineOptimizerAgent):
            def __init__(self):
                custom_handlers = {
                    "AUDIT_PIPELINE": 123,
                    "OPTIMIZE_PIPELINE": self._optimize_pipeline,
                    "ESTABLISH_PIPELINE_SECURITY": self._establish_pipeline_security
                }
                super().__init__(AgentRole.PIPELINE_OPTIMIZER, custom_handlers)
        
        with pytest.raises(TypeError):
            MockAgent()

    def test_error_case_invalid_handler_name(self):
        class MockAgent(PipelineOptimizerAgent):
            def __init__(self):
                custom_handlers = {
                    "UNKNOWN_HANDLER": self._audit_pipeline,
                    "OPTIMIZE_PIPELINE": self._optimize_pipeline,
                    "ESTABLISH_PIPELINE_SECURITY": self._establish_pipeline_security
                }
                super().__init__(AgentRole.PIPELINE_OPTIMIZER, custom_handlers)
        
        with pytest.raises(ValueError):
            MockAgent()

    def test_async_behavior(self):
        class AsyncMock(PipelineOptimizerAgent):
            async def _audit_pipeline(self):
                pass

            async def _optimize_pipeline(self):
                pass

            async def _establish_pipeline_security(self):
                pass
        
        mock_agent = AsyncMock()
        assert isinstance(mock_agent.role, AgentRole)
        assert "AUDIT_PIPELINE" in mock_agent.handlers
        assert "OPTIMIZE_PIPELINE" in mock_agent.handlers
        assert "ESTABLISH_PIPELINE_SECURITY" in mock_agent.handlers