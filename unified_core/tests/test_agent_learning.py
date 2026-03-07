import pytest
from unittest.mock import patch, MagicMock

# Assuming AgentLearningHub is defined somewhere in the same file or imported
from unified_core.agent_learning import AgentLearningHub, get_learning_hub

class TestGetLearningHub:

    @pytest.fixture(autouse=True)
    def setup(self):
        global _hub_instance
        _hub_instance = None  # Reset the global variable before each test

    def test_happy_path(self):
        hub = get_learning_hub()
        assert isinstance(hub, AgentLearningHub)

    def test_edge_cases(self):
        # Since there are no explicit parameters to pass, edge cases like empty, None, or boundaries do not apply here.
        # The function does not accept any arguments, so we can't really test those cases.
        pass

    def test_error_cases(self):
        # There are no error cases to handle since the function doesn't take any parameters and always returns an instance.
        pass

    def test_async_behavior(self):
        # This function does not involve any asynchronous operations.
        pass

    def test_singleton_behavior(self):
        first_call = get_learning_hub()
        second_call = get_learning_hub()
        assert first_call is second_call

    def test_mocked_instance_creation(self):
        with patch('unified_core.agent_learning.AgentLearningHub', new_callable=MagicMock) as mock_hub:
            instance = get_learning_hub()
            mock_hub.assert_called_once()
            assert instance == mock_hub.return_value

    def test_reset_global_instance(self):
        first_call = get_learning_hub()
        global _hub_instance
        _hub_instance = None  # Simulate resetting the global instance
        second_call = get_learning_hub()
        assert first_call != second_call  # New instance should be created after reset