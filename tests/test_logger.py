import pytest
from src.logger import Logger

def test_logger_instance_singleton():
    """Test that a new instance of Logger is created and stored as a class variable."""
    assert Logger._instance is None, "Instance should not exist before instantiation"
    logger1 = Logger()
    assert Logger._instance is not None, "Instance should be created on first instantiation"
    assert id(logger1) == id(Logger()), "New instances should return the same instance"

def test_logger_attributes():
    """Test that the logger attributes are correctly initialized."""
    logger = Logger()
    assert hasattr(logger, 'logger'), "Logger attribute should be initialized"
    assert isinstance(logger.logger, logging.Logger), "Logger should be an instance of logging.Logger"
    handler = next(iter(logger.logger.handlers))
    assert isinstance(handler, logging.StreamHandler), "StreamHandler should be added to the logger"
    assert handler.level == logging.DEBUG, "Default log level should be DEBUG"

def test_logger_method():
    """Test that a method call on the logger works correctly."""
    logger = Logger()
    logger.logger.info("This is a test message")
    # Assuming you have a way to capture logs for testing
    # For example, using logging's CaptureHandler from pytest-logging
    # or by checking if a file has been written to.
    # Here we'll assume there's a method to check the log output
    assert logger.check_log_contains("This is a test message"), "Log should contain the test message"

def test_logger_with_existing_instance():
    """Test that subsequent instantiations return the same instance."""
    logger1 = Logger()
    logger2 = Logger()
    assert id(logger1) == id(logger2), "Subsequent instances should be the same"

# Assuming you have a way to capture and verify log output
# def test_logger_check_log_contains(message):
#     # Your implementation here