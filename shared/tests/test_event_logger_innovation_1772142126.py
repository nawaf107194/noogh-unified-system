import pytest

from src.shared.event_logger import EventLogger

def test_init_happy_path():
    logger = EventLogger(log_file='events.log')
    assert logger.log_file == 'events.log'

def test_init_empty_log_file():
    logger = EventLogger()
    assert logger.log_file == 'events.log'  # Default value should be used if None is provided

def test_init_none_log_file():
    logger = EventLogger(log_file=None)
    assert logger.log_file == 'events.log'  # Default value should be used if None is provided

def test_init_boundary_case_long_string():
    long_string = "a" * 1024 * 1024  # A very long string
    logger = EventLogger(log_file=long_string)
    assert logger.log_file == long_string

def test_init_invalid_log_file_type():
    with pytest.raises(TypeError):
        EventLogger(log_file=123)  # Should raise TypeError if the log_file is not a string

def test_init_empty_string_as_log_file():
    logger = EventLogger(log_file='')
    assert logger.log_file == 'events.log'  # Default value should be used if an empty string is provided

# Async behavior tests are not applicable as the __init__ method does not contain any asynchronous operations