import pytest
from typing import List, Dict, Any
from gateway.app.console.policy import evaluate, Decision

# Mock data
ROLE_SCOPES = {
    'admin': {'read', 'write', 'execute'},
    'user': {'read'}
}
ALLOWED_ACTIONS = {
    'read_data': {"scope": "read"},
    'write_data': {"scope": "write"},
    'execute_model': {"scope": "execute"}
}

@pytest.fixture
def mock_roles():
    return ROLE_SCOPES

@pytest.fixture
def mock_allowed_actions():
    return ALLOWED_ACTIONS

@pytest.mark.parametrize("role,mode,requested_actions,expected", [
    ('admin', 'ANALYZE', [{"action": "read_data"}], Decision(True, "read-only mode", "ANALYZE", [])),
    ('admin', 'EXECUTE', [{"action": "execute_model", "args": {"model_id": 1}}], Decision(True, "allowed", "EXECUTE", [{"action": "execute_model", "args": {"model_id": 1}}])),
    ('user', 'EXECUTE', [{"action": "write_data"}], Decision(False, "insufficient scope for write_data (need write)", "EXECUTE", [])),
])
def test_evaluate_happy_path(role, mode, requested_actions, expected):
    result = evaluate(role, mode, requested_actions)
    assert result == expected

@pytest.mark.parametrize("role,mode,requested_actions", [
    ('nonexistent_role', 'ANALYZE', []),
    ('admin', 'INVALID_MODE', []),
    ('admin', 'EXECUTE', [{}]),
    ('admin', 'EXECUTE', [None]),
])
def test_evaluate_edge_cases(role, mode, requested_actions):
    with pytest.raises(AssertionError):
        result = evaluate(role, mode, requested_actions)
        assert isinstance(result, Decision)

@pytest.mark.parametrize("role,mode,requested_actions", [
    ('admin', 'EXECUTE', [{"action": "unknown_action"}]),
    ('admin', 'EXECUTE', [{"action": "read_data", "args": "not a dict"}]),
])
def test_evaluate_error_cases(role, mode, requested_actions):
    result = evaluate(role, mode, requested_actions)
    assert not result.allowed

@pytest.mark.asyncio
async def test_evaluate_async_behavior():
    # Since the function does not have any asynchronous behavior,
    # we just call it normally to ensure it works as expected.
    result = await evaluate('admin', 'EXECUTE', [{"action": "execute_model", "args": {"model_id": 1}}])
    assert result == Decision(True, "allowed", "EXECUTE", [{"action": "execute_model", "args": {"model_id": 1}}])