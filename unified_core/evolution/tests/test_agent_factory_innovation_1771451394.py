import pytest
from unittest.mock import patch, MagicMock
from unified_core.evolution.agent_factory import get_agent_factory, AgentFactory

class TestAgentFactory:

    @pytest.fixture(autouse=True)
    def setup(self):
        global _factory_instance
        _factory_instance = None  # Reset the global variable before each test

    def test_happy_path(self):
        factory = get_agent_factory()
        assert isinstance(factory, AgentFactory)

    def test_edge_cases(self):
        # Since there are no parameters, edge cases like empty or None don't apply
        pass

    def test_error_cases(self):
        # Since the function doesn't take any arguments, there's no way to pass invalid inputs
        pass

    def test_async_behavior(self):
        # The function does not involve async operations, so this test is not applicable
        pass

    def test_singleton_behavior(self):
        factory1 = get_agent_factory()
        factory2 = get_agent_factory()
        assert factory1 is factory2

    def test_factory_creation(self):
        with patch('unified_core.evolution.agent_factory.AgentFactory') as MockFactory:
            instance = MockFactory.return_value
            factory = get_agent_factory()
            MockFactory.assert_called_once()
            assert factory is instance

    def test_reset_global_instance(self):
        global _factory_instance
        factory = get_agent_factory()
        _factory_instance = None
        new_factory = get_agent_factory()
        assert factory is not new_factory