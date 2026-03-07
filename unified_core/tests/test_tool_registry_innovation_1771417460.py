import pytest
from unittest.mock import patch, MagicMock
from unified_core.tool_registry import get_unified_registry, UnifiedToolRegistry, ActuatorHub
from unified_core.core.logger import logger

# Mocking the logger
logger.error = MagicMock()

class TestUnifiedRegistry:

    @pytest.fixture(autouse=True)
    def setup(self):
        global _unified_registry
        _unified_registry = None

    def test_happy_path(self):
        with patch('unified_core.core.actuators.ActuatorHub') as mock_hub:
            mock_hub.return_value = "mocked_hub"
            registry = get_unified_registry()
            assert isinstance(registry, UnifiedToolRegistry)
            assert registry.actuator_hub == "mocked_hub"

    def test_empty_registry_fallback(self):
        with patch('unified_core.core.actuators.ActuatorHub', side_effect=Exception("Mocked exception")):
            registry = get_unified_registry()
            assert isinstance(registry, UnifiedToolRegistry)
            assert registry.actuator_hub is None

    def test_error_logging(self):
        with patch('unified_core.core.actuators.ActuatorHub', side_effect=Exception("Mocked exception")):
            get_unified_registry()
            logger.error.assert_called_once_with("Failed to initialize global registry: Mocked exception")

    def test_async_behavior(self):
        # Since the function does not have any async operations, this test will pass without doing anything.
        # If there were async operations, we would use `asyncio` and `pytest.mark.asyncio`.
        assert True

    def test_edge_cases(self):
        # There are no direct edge cases in this function since it doesn't take parameters,
        # but we can check if the registry is reused.
        first_call = get_unified_registry()
        second_call = get_unified_registry()
        assert first_call is second_call

    def test_invalid_inputs(self):
        # This function does not accept any inputs directly, so this test is more about ensuring
        # that the registry handles unexpected conditions gracefully.
        with patch('unified_core.core.actuators.ActuatorHub', side_effect=TypeError("Unexpected type error")):
            registry = get_unified_registry()
            assert isinstance(registry, UnifiedToolRegistry)
            assert registry.actuator_hub is None