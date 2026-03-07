import pytest

from unified_core.benchmark_runner import BenchmarkRunner

def test_to_dict_happy_path():
    runner = BenchmarkRunner(
        task_id="123",
        description="Test Task",
        expected_tools=["tool1", "tool2"],
        max_steps=10,
        timeout_seconds=60,
        category="unit_tests"
    )
    result = runner.to_dict()
    assert result == {
        "task_id": "123",
        "description": "Test Task",
        "expected_tools": ["tool1", "tool2"],
        "max_steps": 10,
        "timeout_seconds": 60,
        "category": "unit_tests"
    }

def test_to_dict_empty_values():
    runner = BenchmarkRunner(
        task_id="",
        description="",
        expected_tools=[],
        max_steps=0,
        timeout_seconds=0,
        category=""
    )
    result = runner.to_dict()
    assert result == {
        "task_id": "",
        "description": "",
        "expected_tools": [],
        "max_steps": 0,
        "timeout_seconds": 0,
        "category": ""
    }

def test_to_dict_none_values():
    runner = BenchmarkRunner(
        task_id=None,
        description=None,
        expected_tools=None,
        max_steps=None,
        timeout_seconds=None,
        category=None
    )
    result = runner.to_dict()
    assert result == {
        "task_id": None,
        "description": None,
        "expected_tools": None,
        "max_steps": None,
        "timeout_seconds": None,
        "category": None
    }

def test_to_dict_async_behavior():
    # Assuming there's no async behavior in the to_dict method, this is a placeholder for future expansion
    pass

# Note: There are no error cases or invalid inputs defined in the function, so those tests are not applicable.