import pytest
from unified_core.types import to_dict

def test_to_dict_happy_path():
    result = to_dict(True, "Success", None, 100)
    assert result == {
        "success": True,
        "output": "Success",
        "error": None,
        "execution_time_ms": 100
    }

def test_to_dict_empty_input():
    result = to_dict(None, "", None, 0)
    assert result == {
        "success": None,
        "output": "",
        "error": None,
        "execution_time_ms": 0
    }

def test_to_dict_none_inputs():
    result = to_dict(None, None, None, None)
    assert result == {
        "success": None,
        "output": None,
        "error": None,
        "execution_time_ms": None
    }

def test_to_dict_error_input():
    result = to_dict(False, None, "Error", 200)
    assert result == {
        "success": False,
        "output": None,
        "error": "Error",
        "execution_time_ms": 200
    }