import pytest

def test_convert_to_type_happy_path():
    assert _convert_to_type(123, int) == 123
    assert _convert_to_type(123.45, float) == 123.45
    assert _convert_to_type("hello", str) == "hello"
    assert _convert_to_type(True, bool) is True
    assert _convert_to_type([1, 2, 3], list) == [1, 2, 3]
    assert _convert_to_type({'a': 1}, dict) == {'a': 1}

def test_convert_to_type_edge_cases():
    assert _convert_to_type("", int) == ""
    assert _convert_to_type(None, str) is None
    assert _convert_to_type(0, bool) is False
    assert _convert_to_type([], list) == []
    assert _convert_to_type({}, dict) == {}

def test_convert_to_type_error_cases():
    assert _convert_to_type("abc", int) == "abc"
    assert _convert_to_type("123.45a", float) == "123.45a"
    assert _convert_to_type("hello", bool) is True
    assert _convert_to_type(["a", "b"], dict) == ["a", "b"]
    assert _convert_to_type({"a": 1, "b": 2}, list) == {"a": 1, "b": 2}

def test_convert_to_type_invalid_target_type():
    assert _convert_to_type(123, type(None)) is 123