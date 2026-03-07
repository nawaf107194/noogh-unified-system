import pytest
from typing import List, Dict, Any
from gateway.app.console.policy import evaluate, Decision

# Mock data
ROLE_SCOPES = {
    "admin": {"execute", "read"},
    "user": {"read"}
}
ALLOWED_ACTIONS = {
    "read_data": {"scope": "read"},
    "write_data": {"scope": "execute"}
}

# Test setup
@pytest.fixture(autouse=True)
def setup():
    global ROLE_SCOPES, ALLOWED_ACTIONS
    ROLE_SCOPES = {
        "admin": {"execute", "read"},
        "user": {"read"}
    }
    ALLOWED_ACTIONS = {
        "read_data": {"scope": "read"},
        "write_data": {"scope": "execute"}
    }

# Test cases
def test_happy_path_analyze_mode():
    role = "admin"
    mode = "ANALYZE"
    requested_actions = [{"action": "read_data", "args": {"path": "/data"}}]
    decision = evaluate(role, mode, requested_actions)
    assert decision.allowed is True
    assert decision.reason == "read-only mode"
    assert decision.sanitized_actions == []

def test_happy_path_execute_mode_with_valid_scopes():
    role = "admin"
    mode = "EXECUTE"
    requested_actions = [
        {"action": "read_data", "args": {"path": "/data"}},
        {"action": "write_data", "args": {"path": "/output"}}
    ]
    decision = evaluate(role, mode, requested_actions)
    assert decision.allowed is True
    assert decision.reason == "allowed"
    assert len(decision.sanitized_actions) == 2

def test_edge_case_empty_requested_actions():
    role = "admin"
    mode = "EXECUTE"
    requested_actions = []
    decision = evaluate(role, mode, requested_actions)
    assert decision.allowed is True
    assert decision.reason == "allowed"
    assert decision.sanitized_actions == []

def test_edge_case_none_role():
    role = None
    mode = "EXECUTE"
    requested_actions = [{"action": "read_data", "args": {"path": "/data"}}]
    with pytest.raises(TypeError):
        evaluate(role, mode, requested_actions)

def test_error_case_invalid_mode():
    role = "admin"
    mode = "INVALID_MODE"
    requested_actions = [{"action": "read_data", "args": {"path": "/data"}}]
    decision = evaluate(role, mode, requested_actions)
    assert decision.allowed is False
    assert decision.reason == "invalid mode"

def test_error_case_insufficient_scope():
    role = "user"
    mode = "EXECUTE"
    requested_actions = [{"action": "write_data", "args": {"path": "/output"}}]
    decision = evaluate(role, mode, requested_actions)
    assert decision.allowed is False
    assert decision.reason == "insufficient scope for write_data (need execute)"

def test_error_case_not_allowlisted_action():
    role = "admin"
    mode = "EXECUTE"
    requested_actions = [{"action": "unknown_action", "args": {"path": "/output"}}]
    decision = evaluate(role, mode, requested_actions)
    assert decision.allowed is False
    assert decision.reason == "action not allowlisted: unknown_action"

# Note: No async behavior to test as the provided function does not involve any asynchronous operations.