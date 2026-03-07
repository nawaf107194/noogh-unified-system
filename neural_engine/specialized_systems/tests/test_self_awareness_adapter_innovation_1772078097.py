import pytest

def test_happy_path():
    executions = [
        {"payload": {"success": True, "action": "action1"}},
        {"payload": {"success": False, "action": "action2"}},
        {"payload": {"success": True, "action": "action1"}}
    ]
    result = _analyze_executions(executions)
    assert result == {
        "total_executions": 3,
        "successful": 2,
        "failed": 1,
        "success_rate": 0.6666666666666666,
        "top_executed_actions": [('action1', 2), ('action2', 1)]
    }

def test_empty_input():
    result = _analyze_executions([])
    assert result == {
        "total_executions": 0,
        "successful": 0,
        "failed": 0,
        "success_rate": 0.0,
        "top_executed_actions": []
    }

def test_none_input():
    result = _analyze_executions(None)
    assert result is None

def test_boundary_values():
    executions = [{"payload": {"success": True, "action": "action1"}}]
    result = _analyze_executions(executions)
    assert result == {
        "total_executions": 1,
        "successful": 1,
        "failed": 0,
        "success_rate": 1.0,
        "top_executed_actions": [('action1', 1)]
    }

def test_invalid_input():
    executions = [{"payload": {"success": None, "action": "action1"}}]
    result = _analyze_executions(executions)
    assert result == {
        "total_executions": 1,
        "successful": 0,
        "failed": 0,
        "success_rate": 0.0,
        "top_executed_actions": [('action1', 1)]
    }