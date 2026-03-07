import pytest
from centralized_logging_1771346850 import CentralizedLogger
import logging
from logging.handlers import TimedRotatingFileHandler

@pytest.fixture
def logger_instance():
    return CentralizedLogger('test_logger')

def test_happy_path(logger_instance):
    assert isinstance(logger_instance.logger, logging.Logger)
    assert logger_instance.logger.level == logging.INFO
    assert len(logger_instance.logger.handlers) == 1  # Only console handler by default

def test_with_log_file(tmpdir, logger_instance):
    log_file = tmpdir.join("test.log")
    logger_instance = CentralizedLogger('test_logger', log_file=str(log_file))
    assert len(logger_instance.logger.handlers) == 2  # Both console and file handlers
    assert isinstance(logger_instance.logger.handlers[1], TimedRotatingFileHandler)

def test_empty_name():
    with pytest.raises(TypeError):
        CentralizedLogger()

def test_none_level():
    logger_instance = CentralizedLogger('test_logger', level=None)
    assert logger_instance.logger.level == logging.INFO

def test_invalid_level():
    with pytest.raises(ValueError):
        CentralizedLogger('test_logger', level="INVALID")

def test_custom_log_format():
    custom_format = '%(asctime)s - Custom Format'
    logger_instance = CentralizedLogger('test_logger', log_format=custom_format)
    assert logger_instance.logger.handlers[0].formatter._fmt == custom_format

def test_nonexistent_log_file(tmpdir):
    log_file = tmpdir.join("nonexistent_dir/test.log")
    logger_instance = CentralizedLogger('test_logger', log_file=str(log_file))
    assert len(logger_instance.logger.handlers) == 2  # Both console and file handlers
    assert isinstance(logger_instance.logger.handlers[1], TimedRotatingFileHandler)

def test_async_behavior(logger_instance):
    # Since logging is generally synchronous in nature, this test would not apply unless there's an async component.
    pass