import pytest
from unittest.mock import patch, MagicMock
from logging import INFO, DEBUG, WARNING, ERROR, CRITICAL

# Assuming StructuredLogger is defined elsewhere in the module
from unified_core.observability.logger import get_logger, StructuredLogger

@pytest.fixture
def mock_structured_logger():
    with patch('unified_core.observability.logger.StructuredLogger', autospec=True) as MockStructuredLogger:
        yield MockStructuredLogger

class TestGetLogger:

    def test_happy_path(self, mock_structured_logger):
        # Normal input
        service_name = "test_service"
        level = INFO
        expected_logger = mock_structured_logger.return_value
        actual_logger = get_logger(service_name, level)
        assert actual_logger == expected_logger
        mock_structured_logger.assert_called_once_with(service_name, level)

    def test_empty_service_name(self, mock_structured_logger):
        # Empty string as service name
        service_name = ""
        level = INFO
        expected_logger = mock_structured_logger.return_value
        actual_logger = get_logger(service_name, level)
        assert actual_logger == expected_logger
        mock_structured_logger.assert_called_once_with(service_name, level)

    def test_none_service_name(self, mock_structured_logger):
        # None as service name
        service_name = None
        level = INFO
        expected_logger = mock_structured_logger.return_value
        actual_logger = get_logger(service_name, level)
        assert actual_logger == expected_logger
        mock_structured_logger.assert_called_once_with(service_name, level)

    @pytest.mark.parametrize("level", [DEBUG, WARNING, ERROR, CRITICAL])
    def test_different_levels(self, mock_structured_logger, level):
        # Different logging levels
        service_name = "test_service"
        expected_logger = mock_structured_logger.return_value
        actual_logger = get_logger(service_name, level)
        assert actual_logger == expected_logger
        mock_structured_logger.assert_called_once_with(service_name, level)

    def test_invalid_level_type(self):
        # Invalid type for level
        service_name = "test_service"
        level = "not_a_level"
        with pytest.raises(TypeError):
            get_logger(service_name, level)

    def test_async_behavior(self, event_loop):
        # Since get_logger is not async, we can just run it in an async context
        async def test_coroutine():
            service_name = "async_test_service"
            level = INFO
            logger = await event_loop.run_in_executor(None, get_logger, service_name, level)
            assert isinstance(logger, StructuredLogger)

        event_loop.run_until_complete(test_coroutine())