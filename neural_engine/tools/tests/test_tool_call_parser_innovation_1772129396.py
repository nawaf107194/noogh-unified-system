import pytest
from typing import List, Tuple, Dict, Any
import json

class ToolCallParser:
    JSON_PATTERN = re.compile(r'"tool":"(.*?)","args":\s*(.*?)\s*')

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

# Test code
def test_parse_json_call_happy_path():
    text = '{"tool":"read_file","args":{"path":"/tmp/a.txt"}}'
    expected_output = [('read_file', {'path': '/tmp/a.txt'})]
    assert parse_json_call(text) == expected_output

def test_parse_json_call_multiple_calls():
    text = ('{"tool":"read_file","args":{"path":"/tmp/a.txt"}} '
            '{"tool":"write_file","args":{"content":"hello world"}}')
    expected_output = [
        ('read_file', {'path': '/tmp/a.txt'}),
        ('write_file', {'content': 'hello world'})
    ]
    assert parse_json_call(text) == expected_output

def test_parse_json_call_empty_input():
    text = ''
    expected_output = []
    assert parse_json_call(text) == expected_output

def test_parse_json_call_none_input():
    text = None
    expected_output = []
    assert parse_json_call(text) == expected_output

def test_parse_json_call_invalid_format():
    text = '{"tool":"read_file","args}:{path":"/tmp/a.txt"}}'
    expected_output = []
    assert parse_json_call(text) == expected_output

def test_parse_json_call_missing_args():
    text = '{"tool":"read_file"}'
    expected_output = [('read_file', {})]
    assert parse_json_call(text) == expected_output

def test_parse_json_call_extra_spaces():
    text = '  {"tool":"read_file","args":{"path":"/tmp/a.txt"}}  '
    expected_output = [('read_file', {'path': '/tmp/a.txt'})]
    assert parse_json_call(text) == expected_output