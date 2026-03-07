import pytest
from unittest.mock import patch

class TestAgentLearningHubInit:

    @pytest.fixture
    def agent(self):
        from unified_core.agent_learning import AgentLearningHub
        return AgentLearningHub()

    def test_happy_path(self, agent):
        assert agent._neuron_fabric is None
        assert agent._message_bus is None
        assert isinstance(agent._knowledge_log, list)
        assert len(agent._knowledge_log) == 0
        assert agent._max_log == 200
        assert agent.total_shared == 0
        assert agent.total_consumed == 0

    def test_edge_cases(self, agent):
        # Testing edge cases might not be applicable since the init method does not take any parameters.
        # However, we can check if the internal state remains as expected even in edge scenarios.
        assert agent._neuron_fabric is None  # Checking for default None value
        assert agent._message_bus is None  # Checking for default None value
        assert len(agent._knowledge_log) == 0  # Empty list at initialization

    def test_error_cases(self, agent):
        # Since the constructor does not accept any parameters, there are no error cases to handle.
        # This test case is more of a placeholder or could be used to test future modifications.
        pass

    def test_async_behavior(self, agent):
        # The given `__init__` method does not have any asynchronous behavior.
        # If in the future it gets updated with async methods, this test can be updated accordingly.
        pass

    def test_logger_info_called(self):
        from unified_core.agent_learning import AgentLearningHub
        with patch('unified_core.agent_learning.logger') as mock_logger:
            agent = AgentLearningHub()
            mock_logger.info.assert_called_once_with("✅ AgentLearningHub initialized")