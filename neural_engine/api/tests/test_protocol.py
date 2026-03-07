import pytest

from neural_engine.api.protocol import validate_action


def test_validate_action_happy_path():
    valid_actions = ["ExecuteCode", "ExecuteShell", "ShellExecutor", "RecallMemory", "StoreMemory", "Dream"]
    for action in valid_actions:
        assert validate_action(action) == action


def test_validate_action_edge_case_empty_string():
    with pytest.raises(ValueError, match="Action '' is not a valid tool. Allowed: .*"):
        validate_action('')


def test_validate_action_edge_case_none():
    with pytest.raises(ValueError, match="Action 'None' is not a valid tool. Allowed: .*"):
        validate_action(None)


def test_validate_action_error_case_invalid_input():
    invalid_action = "InvalidAction"
    with pytest.raises(ValueError, match=f"Action '{invalid_action}' is not a valid tool. Allowed: .*"):
        validate_action(invalid_action)