import pytest
from gateway.app.console.policy import evaluate, Decision

@pytest.mark.parametrize("role, mode, requested_actions, expected", [
    ("admin", "EXECUTE", [{"action": "read"}, {"action": "write"}], Decision(True, "allowed", "EXECUTE", [{"action": "read", "args": {}}, {"action": "write", "args": {}}])),
    ("user", "EXECUTE", [{"action": "read"}, {"action": "delete"}], Decision(False, "insufficient scope for delete (need admin)", "EXECUTE", [])),
    ("guest", "ANALYZE", [], Decision(True, "read-only mode", "ANALYZE", [])),
    ("admin", "OBSERVE", [{"action": "read"}, {"action": "write"}], Decision(True, "read-only mode", "ANALYZE", [])),
    ("admin", "EXECUTE", [], Decision(False, "invalid mode", "EXECUTE", [])),
    (None, "EXECUTE", [{"action": "read"}, {"action": "write"}], Decision(False, "action not allowlisted: None", "EXECUTE", [])),
    ("admin", "EXECUTE", [{"action": "unknown"}, {"action": "write"}], Decision(False, "action not allowlisted: unknown", "EXECUTE", [])),
    ("user", "EXECUTE", [{"action": "read", "args": {"key": "value"}}], Decision(True, "allowed", "EXECUTE", [{"action": "read", "args": {"key": "value"}}]))
])
def test_evaluate(role, mode, requested_actions, expected):
    result = evaluate(role, mode, requested_actions)
    assert result == expected