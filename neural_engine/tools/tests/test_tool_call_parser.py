import pytest
from typing import List, Tuple, Dict, Any
import re
import json

# Mocking the ToolCallParser class and its JSON_PATTERN attribute
class ToolCallParser:
    JSON_PATTERN = re.compile(r'\{"tool":"(?P<tool_name>[^"]+)","args":(?P<args_json>\{.*?\})\}')

def parse_json_call(text: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Parse JSON tool calls
    Format: {"tool":"read_file","args":{"path":"/tmp/a.txt"}}
    
    Returns:
        List of (tool_name, args_dict) tuples
    """
    calls = []
    
    for match in ToolCallParser.JSON_PATTERN.finditer(text):
        try:
            tool_name = match.group(1)
            args_json = match.group(2)
            args = json.loads(args_json)
            calls.append((tool_name, args))
        except json.JSONDecodeError:
            continue
    
    return calls

# Test cases
def test_parse_json_call_happy_path():
    text = '{"tool":"read_file","args":{"path":"/tmp/a.txt"}}'
    expected = [("read_file", {"path": "/tmp/a.txt"})]
    assert parse_json_call(text) == expected

def test_parse_json_call_multiple_calls():
    text = '{"tool":"read_file","args":{"path":"/tmp/a.txt"}}, {"tool":"write_file","args":{"path":"/tmp/b.txt", "content":"Hello World!"}}'
    expected = [
        ("read_file", {"path": "/tmp/a.txt"}),
        ("write_file", {"path": "/tmp/b.txt", "content": "Hello World!"})
    ]
    assert parse_json_call(text) == expected

def test_parse_json_call_empty_string():
    text = ""
    expected = []
    assert parse_json_call(text) == expected

def test_parse_json_call_none_input():
    with pytest.raises(TypeError):
        parse_json_call(None)

def test_parse_json_call_invalid_json():
    text = '{"tool":"read_file","args":{"path":"/tmp/a.txt"}'
    expected = []
    assert parse_json_call(text) == expected

def test_parse_json_call_malformed_tool_name():
    text = '{"tool":"read_file","args":{"path":"/tmp/a.txt"}} {"tool":read_file,"args":{"path":"/tmp/a.txt"}}'
    expected = [("read_file", {"path": "/tmp/a.txt"})]
    assert parse_json_call(text) == expected

def test_parse_json_call_malformed_args():
    text = '{"tool":"read_file","args":{"path":"/tmp/a.txt"}} {"tool":"write_file","args":{"path":"/tmp/a.txt", "content":}}'
    expected = [("read_file", {"path": "/tmp/a.txt"})]
    assert parse_json_call(text) == expected

def test_parse_json_call_async_behavior():
    # Since the function is synchronous and does not involve any async operations,
    # there's no need to test for async behavior.
    pass