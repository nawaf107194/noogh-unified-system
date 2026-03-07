import pytest
from unittest.mock import patch, MagicMock

from agents.pipeline_optimizer_agent import PipelineOptimizerAgent, AgentRole, logger

class TestPipelineOptimizerAgent:

    @pytest.fixture
    def agent(self):
        with patch("agents.pipeline_optimizer_agent.logger") as mock_logger:
            return PipelineOptimizerAgent()

    def test_init_happy_path(self, agent):
        assert agent.role == AgentRole.PIPELINE_OPTIMIZER
        assert "AUDIT_PIPELINE" in agent.custom_handlers
        assert "OPTIMIZE_PIPELINE" in agent.custom_handlers
        assert "ESTABLISH_PIPELINE_SECURITY" in agent.custom_handlers
        assert logger.info.call_args_list[-1][0] == ("✅ PipelineOptimizerAgent initialized",)

    def test_init_no_custom_handlers(self, agent):
        with patch("agents.pipeline_optimizer_agent.AgentRole.PIPELINE_OPTIMIZER", new_callable=MagicMock) as mock_role:
            mock_role.value = 2
            agent = PipelineOptimizerAgent()
            assert agent.role == 2
            assert not agent.custom_handlers

    def test_init_empty_custom_handlers(self, agent):
        with patch("agents.pipeline_optimizer_agent.logger") as mock_logger:
            custom_handlers = {}
            agent = PipelineOptimizerAgent(custom_handlers=custom_handlers)
            assert agent.role == AgentRole.PIPELINE_OPTIMIZER
            assert not agent.custom_handlers
            assert logger.info.call_args_list[-1][0] == ("✅ PipelineOptimizerAgent initialized",)

    def test_init_none_custom_handlers(self, agent):
        with patch("agents.pipeline_optimizer_agent.logger") as mock_logger:
            custom_handlers = None
            agent = PipelineOptimizerAgent(custom_handlers=custom_handlers)
            assert agent.role == AgentRole.PIPELINE_OPTIMIZER
            assert not agent.custom_handlers
            assert logger.info.call_args_list[-1][0] == ("✅ PipelineOptimizerAgent initialized",)

    def test_init_invalid_custom_handlers(self, agent):
        with patch("agents.pipeline_optimizer_agent.logger") as mock_logger:
            custom_handlers = "invalid"
            with pytest.raises(TypeError):
                PipelineOptimizerAgent(custom_handlers=custom_handlers)