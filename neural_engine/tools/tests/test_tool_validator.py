import pytest
from neural_engine.tools.tool_validator import validate_tool_args, ValidationError
from typing import Dict, Any

def _validate_value(value: Any, depth: int = 0, max_depth: int = MAX_DICT_DEPTH, max_string_len: int = MAX_STRING_LENGTH) -> Any:
    if isinstance(value, dict):
        if depth >= max_depth:
            raise RecursionError("Max recursion depth exceeded")
        return {k: _validate_value(v, depth + 1, max_depth, max_string_len) for k, v in value.items()}
    elif isinstance(value, list):
        if depth >= max_depth:
            raise RecursionError("Max recursion depth exceeded")
        return [_validate_value(v, depth + 1, max_depth, max_string_len) for v in value]
    elif isinstance(value, str):
        if len(value) > max_string_len:
            raise ValueError(f"String too long: {value}")
        if "\0" in value:
            raise ValueError("Null bytes detected")
    return value

@pytest.mark.parametrize(
    "tool_name, args, expected",
    [
        ("tool1", {"a": 1, "b": 2}, {"a": 1, "b": 2}),
        ("tool2", {"x": {"y": 3}}, {"x": {"y": 3}}),
        ("tool3", {"max_depth": 1, "args": {}}, {}),
    ]
)
def test_validate_tool_args_happy_path(tool_name, args, expected):
    result = validate_tool_args(tool_name, args)
    assert result == expected

@pytest.mark.parametrize(
    "tool_name, args",
    [
        ("tool4", None),
        ("tool5", []),
        ("tool6", ""),
    ]
)
def test_validate_tool_args_edge_cases(tool_name, args):
    with pytest.raises(ValidationError) as exc_info:
        validate_tool_args(tool_name, args)
    assert str(exc_info.value).startswith("Tool args must be dict")

@pytest.mark.parametrize(
    "tool_name, args",
    [
        ("tool7", {"a": "x" * 1000}),
        ("tool8", {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": "x" * 1000}}}}}}}}}},
    ]
)
def test_validate_tool_args_error_cases(tool_name, args):
    with pytest.raises(ValidationError) as exc_info:
        validate_tool_args(tool_name, args)
    assert str(exc_info.value).startswith("String too long") or \
           "Max recursion depth exceeded" in str(exc_info.value)

@pytest.mark.parametrize(
    "tool_name, args",
    [
        ("tool9", {"a": "\0"}),
        ("tool10", {"a": {"b": "\0"}}),
    ]
)
def test_validate_tool_args_error_cases_null_bytes(tool_name, args):
    with pytest.raises(ValidationError) as exc_info:
        validate_tool_args(tool_name, args)
    assert "Null bytes detected" in str(exc_info.value)