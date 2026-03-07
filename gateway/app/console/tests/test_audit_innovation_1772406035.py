import pytest
from datetime import time
from typing import Optional

def audit_event_signed(event_type: str, data: dict) -> str:
    # Mock implementation to return the event type as the audit event ID
    return event_type

@pytest.fixture
def mock_audit_event_signed():
    from unittest.mock import patch
    with patch('gateway.app.console.audit.audit_event_signed') as mock:
        yield mock

def test_happy_path(mock_audit_event_signed):
    operation = "store"
    session_id = "session123"
    user_scope = "admin"
    memory_id = "memory456"

    result = audit_memory_access(operation, session_id, user_scope, memory_id=memory_id)

    expected_data = {
        "operation": operation,
        "session_id": session_id,
        "user_scope": user_scope,
        "query": None,
        "memory_id": memory_id,
        "timestamp": time.time(),
    }
    
    mock_audit_event_signed.assert_called_once_with("memory_access", expected_data)
    assert result == "memory_access"

def test_edge_case_empty_query(mock_audit_event_signed):
    operation = "recall"
    session_id = "session123"
    user_scope = "readonly"
    query = ""

    result = audit_memory_access(operation, session_id, user_scope, query=query)

    expected_data = {
        "operation": operation,
        "session_id": session_id,
        "user_scope": user_scope,
        "query": "",
        "memory_id": None,
        "timestamp": time.time(),
    }
    
    mock_audit_event_signed.assert_called_once_with("memory_access", expected_data)
    assert result == "memory_access"

def test_edge_case_none_query(mock_audit_event_signed):
    operation = "recall"
    session_id = "session123"
    user_scope = "readonly"
    query = None

    result = audit_memory_access(operation, session_id, user_scope, query=query)

    expected_data = {
        "operation": operation,
        "session_id": session_id,
        "user_scope": user_scope,
        "query": None,
        "memory_id": None,
        "timestamp": time.time(),
    }
    
    mock_audit_event_signed.assert_called_once_with("memory_access", expected_data)
    assert result == "memory_access"

def test_edge_case_empty_memory_id(mock_audit_event_signed):
    operation = "store"
    session_id = "session123"
    user_scope = "admin"
    memory_id = ""

    result = audit_memory_access(operation, session_id, user_scope, memory_id=memory_id)

    expected_data = {
        "operation": operation,
        "session_id": session_id,
        "user_scope": user_scope,
        "query": None,
        "memory_id": "",
        "timestamp": time.time(),
    }
    
    mock_audit_event_signed.assert_called_once_with("memory_access", expected_data)
    assert result == "memory_access"

def test_edge_case_none_memory_id(mock_audit_event_signed):
    operation = "store"
    session_id = "session123"
    user_scope = "admin"
    memory_id = None

    result = audit_memory_access(operation, session_id, user_scope, memory_id=memory_id)

    expected_data = {
        "operation": operation,
        "session_id": session_id,
        "user_scope": user_scope,
        "query": None,
        "memory_id": None,
        "timestamp": time.time(),
    }
    
    mock_audit_event_signed.assert_called_once_with("memory_access", expected_data)
    assert result == "memory_access"

def test_error_case_invalid_operation(mock_audit_event_signed):
    operation = "invalid"
    session_id = "session123"
    user_scope = "admin"
    memory_id = "memory456"

    with pytest.raises(ValueError) as exc_info:
        audit_memory_access(operation, session_id, user_scope, memory_id=memory_id)
    
    assert exc_info.type == ValueError
    mock_audit_event_signed.assert_not_called()