import pytest

from gateway.app.console.policy import evaluate, Decision

def test_happy_path():
    role = "admin"
    mode = "EXECUTE"
    requested_actions = [{"action": "create", "args": {"name": "test"}}]
    expected = Decision(True, "allowed", mode, [{"action": "create", "args": {"name": "test"}}])
    assert evaluate(role, mode, requested_actions) == expected

def test_empty_requested_actions():
    role = "admin"
    mode = "EXECUTE"
    requested_actions = []
    expected = Decision(False, "insufficient scope for create (need admin)", mode, [])
    assert evaluate(role, mode, requested_actions) == expected

def test_mode_analyze():
    role = "user"
    mode = "ANALYZE"
    requested_actions = [{"action": "create", "args": {"name": "test"}}]
    expected = Decision(True, "read-only mode", mode, [])
    assert evaluate(role, mode, requested_actions) == expected

def test_mode_observe():
    role = "user"
    mode = "OBSERVE"
    requested_actions = [{"action": "create", "args": {"name": "test"}}]
    expected = Decision(True, "read-only mode", mode, [])
    assert evaluate(role, mode, requested_actions) == expected

def test_invalid_mode():
    role = "admin"
    mode = "INVALID"
    requested_actions = [{"action": "create", "args": {"name": "test"}}]
    expected = Decision(False, "invalid mode", mode, [])
    assert evaluate(role, mode, requested_actions) == expected

def test_action_not_allowlisted():
    role = "admin"
    mode = "EXECUTE"
    requested_actions = [{"action": "unknown_action", "args": {"name": "test"}}]
    expected = Decision(False, "action not allowlisted: unknown_action", mode, [])
    assert evaluate(role, mode, requested_actions) == expected

def test_insufficient_scope():
    role = "user"
    mode = "EXECUTE"
    requested_actions = [{"action": "create", "args": {"name": "test"}}]
    expected = Decision(False, "insufficient scope for create (need admin)", mode, [])
    assert evaluate(role, mode, requested_actions) == expected

def test_allowlisted_action_with_invalid_args():
    role = "admin"
    mode = "EXECUTE"
    requested_actions = [{"action": "create", "args": {"invalid_arg": "test"}}]
    expected = Decision(False, "insufficient scope for create (need admin)", mode, [])
    assert evaluate(role, mode, requested_actions) == expected