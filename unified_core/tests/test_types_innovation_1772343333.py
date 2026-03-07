import pytest

from unified_core.types import to_dict  # Import the function directly for testing

class MockedResponse:
    def __init__(self, success, output=None, error=None, execution_time_ms=0):
        self.success = success
        self.output = output
        self.error = error
        self.execution_time_ms = execution_time_ms

def test_to_dict_happy_path():
    response = MockedResponse(success=True, output="success", error=None, execution_time_ms=123)
    result = to_dict(response)
    assert result == {
        "success": True,
        "output": "success",
        "error": None,
        "execution_time_ms": 123
    }

def test_to_dict_edge_case_empty():
    response = MockedResponse(success=False, output="", error="empty_output", execution_time_ms=0)
    result = to_dict(response)
    assert result == {
        "success": False,
        "output": "",
        "error": "empty_output",
        "execution_time_ms": 0
    }

def test_to_dict_edge_case_none():
    response = MockedResponse(success=None, output=None, error=None, execution_time_ms=None)
    result = to_dict(response)
    assert result == {
        "success": None,
        "output": None,
        "error": None,
        "execution_time_ms": None
    }

def test_to_dict_edge_case_boundaries():
    response = MockedResponse(success=True, output="boundary", error=None, execution_time_ms=1000)
    result = to_dict(response)
    assert result == {
        "success": True,
        "output": "boundary",
        "error": None,
        "execution_time_ms": 1000
    }

def test_to_dict_error_case_invalid_input():
    # Assuming the function does not raise exceptions for invalid inputs
    with pytest.raises(TypeError):
        response = MockedResponse(success="not_a_bool")
        to_dict(response)