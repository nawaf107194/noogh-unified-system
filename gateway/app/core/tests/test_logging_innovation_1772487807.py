import pytest
import json
from logging import LogRecord
from contextvars import ContextVar, Token

# Mocking get_log_context function to return a fixed context for testing
log_context = ContextVar("log_context")
def mock_get_log_context():
    return log_context.get()

# Fixtures to set up and tear down the log context
@pytest.fixture(autouse=True)
def setup_log_context():
    token = log_context.set({"request_id": "test_trace_id"})
    yield
    log_context.reset(token)

class LoggerAdapter:
    def __init__(self, logger, name):
        self.logger = logger
        self.name = name

    @staticmethod
    def formatTime(record: LogRecord, datefmt=None) -> str:
        return record.asctime  # Simplified for testing purposes

def test_format_happy_path():
    adapter = LoggerAdapter(None, "test_logger")
    record = LogRecord("test_logger", 20, "test_module", 42, "This is a test message", [], None)
    result = adapter.format(record)
    expected = json.dumps({
        "timestamp": record.asctime,
        "level": "INFO",
        "logger": "test_logger",
        "message": "This is a test message",
        "module": "test_module",
        "funcName": "<unknown>",
        "line": 42,
        "trace_id": "test_trace_id"
    })
    assert result == expected

def test_format_empty_record():
    adapter = LoggerAdapter(None, "test_logger")
    record = LogRecord("test_logger", 0, "", 0, "", [], None)
    result = adapter.format(record)
    expected = json.dumps({
        "timestamp": "",
        "level": "",
        "logger": "test_logger",
        "message": "",
        "module": "",
        "funcName": "<unknown>",
        "line": 0,
        "trace_id": "test_trace_id"
    })
    assert result == expected

def test_format_none_record():
    adapter = LoggerAdapter(None, "test_logger")
    record = None
    result = adapter.format(record)
    assert result is None

def test_format_with_extra_fields():
    adapter = LoggerAdapter(None, "test_logger")
    record = LogRecord("test_logger", 20, "test_module", 42, "This is a test message", [], {"extra_field": "value"})
    result = adapter.format(record)
    expected = json.dumps({
        "timestamp": record.asctime,
        "level": "INFO",
        "logger": "test_logger",
        "message": "This is a test message",
        "module": "test_module",
        "funcName": "<unknown>",
        "line": 42,
        "trace_id": "test_trace_id",
        "extra_field": "value"
    })
    assert result == expected

def test_format_no_request_id_in_context():
    log_context.set({})
    adapter = LoggerAdapter(None, "test_logger")
    record = LogRecord("test_logger", 20, "test_module", 42, "This is a test message", [], None)
    result = adapter.format(record)
    expected = json.dumps({
        "timestamp": record.asctime,
        "level": "INFO",
        "logger": "test_logger",
        "message": "This is a test message",
        "module": "test_module",
        "funcName": "<unknown>",
        "line": 42
    })
    assert result == expected