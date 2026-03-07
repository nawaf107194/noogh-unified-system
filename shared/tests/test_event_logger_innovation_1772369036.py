import pytest

from shared.event_logger import EventLogger

def test_event_logger_happy_path():
    logger = EventLogger(log_file='events.log')
    assert logger.log_file == 'events.log'

def test_event_logger_empty_log_file():
    logger = EventLogger(log_file='')
    assert logger.log_file == ''

def test_event_logger_none_log_file():
    logger = EventLogger(log_file=None)
    assert logger.log_file is None

def test_event_logger_boundary_log_file():
    logger = EventLogger(log_file='a' * 1024)  # Assuming a reasonable boundary
    assert logger.log_file == 'a' * 1024

# Error cases are not applicable as the code does not explicitly raise any exceptions