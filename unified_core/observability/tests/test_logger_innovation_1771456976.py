import pytest
from unittest.mock import Mock, patch
from logging import INFO

@pytest.fixture
def logger():
    class Logger:
        def __init__(self):
            self._log = Mock()

        def info(self, message: str, **extra):
            """Info level log"""
            self._log(INFO, message, **extra)
    return Logger()

def test_info_happy_path(logger):
    # Test with normal input
    message = "This is a test message"
    extra = {"key": "value"}
    logger.info(message, **extra)
    logger._log.assert_called_once_with(INFO, message, extra=extra)

def test_info_empty_message(logger):
    # Test with an empty string as message
    message = ""
    logger.info(message)
    logger._log.assert_called_once_with(INFO, message, extra={})

def test_info_none_message(logger):
    # Test with None as message
    message = None
    with pytest.raises(TypeError):
        logger.info(message)

def test_info_invalid_extra(logger):
    # Test with invalid extra parameter
    message = "Test message"
    extra = 123  # Invalid type
    with pytest.raises(TypeError):
        logger.info(message, **extra)

def test_info_no_extra(logger):
    # Test without any extra parameters
    message = "Test message"
    logger.info(message)
    logger._log.assert_called_once_with(INFO, message, extra={})

# Since the given function does not have async behavior, we skip testing for it.
# If the function were to be modified to include async behavior in the future,
# appropriate tests using pytest-asyncio could be added.