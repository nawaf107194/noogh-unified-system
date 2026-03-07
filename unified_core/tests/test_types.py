import pytest
from unified_core.types import to_dict

class MockObject:
    def __init__(self, tool_name, arguments, timestamp):
        self.tool_name = tool_name
        self.arguments = arguments
        self.timestamp = timestamp

def test_to_dict_happy_path():
    obj = MockObject(tool_name="example_tool", arguments={"key": "value"}, timestamp=1633072800)
    result = to_dict(obj)
    expected = {
        "tool_name": "example_tool",
        "arguments": {"key": "value"},
        "timestamp": 1633072800
    }
    assert result == expected

def test_to_dict_edge_case_empty():
    obj = MockObject(tool_name="", arguments={}, timestamp=0)
    result = to_dict(obj)
    expected = {
        "tool_name": "",
        "arguments": {},
        "timestamp": 0
    }
    assert result == expected

def test_to_dict_edge_case_none():
    obj = MockObject(tool_name=None, arguments=None, timestamp=None)
    result = to_dict(obj)
    expected = {
        "tool_name": None,
        "arguments": None,
        "timestamp": None
    }
    assert result == expected

def test_to_dict_error_case_invalid_input():
    # Assuming the code doesn't explicitly raise exceptions for invalid inputs
    obj = MockObject(tool_name=123, arguments=[1, 2, 3], timestamp="not_a_timestamp")
    result = to_dict(obj)
    expected = {
        "tool_name": 123,
        "arguments": [1, 2, 3],
        "timestamp": "not_a_timestamp"
    }
    assert result == expected