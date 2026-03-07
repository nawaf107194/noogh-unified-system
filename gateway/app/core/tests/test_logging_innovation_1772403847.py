import pytest
import logging
from gateway.app.core.logging import format
from contextvars import ContextVar, Token

# Create a sample log record for testing
sample_record = logging.LogRecord(
    name="test_logger",
    level=logging.INFO,
    pathname="/path/to/test.py",
    lineno=42,
    msg="This is a test message",
    args=(),
    exc_info=None,
)

# Sample context variable values
log_context_var = ContextVar("log_context")
sample_context = {"request_id": "12345", "user_id": "user123"}

def test_format_happy_path():
    # Set the context variable for the test
    token = log_context_var.set(sample_context)
    
    try:
        result = format(sample_record)
        assert "timestamp" in result
        assert "level" in result
        assert "logger" in result
        assert "message" in result
        assert "module" in result
        assert "funcName" in result
        assert "line" in result
        assert "trace_id" in result
        assert "user_id" in result
        
        # Check if all keys are present and correctly formatted
        log_record = json.loads(result)
        assert "timestamp" in log_record
        assert "level" in log_record
        assert "logger" in log_record
        assert "message" in log_record
        assert "module" in log_record
        assert "funcName" in log_record
        assert "line" in log_record
        assert "trace_id" in log_record
        assert "user_id" in log_record
    finally:
        # Restore the original context variable value after test
        log_context_var.reset(token)

def test_format_edge_case_empty_log_record():
    empty_record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    )
    
    result = format(empty_record)
    assert "timestamp" in result
    assert "level" in result
    assert "logger" in result
    assert "message" in result
    assert "module" in result
    assert "funcName" in result
    assert "line" in result

def test_format_edge_case_none_log_record():
    result = format(None)
    assert result is None

def test_format_edge_case_boundary_timestamp():
    # Set the timestamp boundary to ensure it handles edge cases
    sample_record.created = 0
    
    result = format(sample_record)
    assert "timestamp" in result

def test_format_error_case_invalid_log_record_type():
    with pytest.raises(TypeError):
        format("not a LogRecord")

# Test async behavior if applicable (if there's any async code inside the function, test it here)