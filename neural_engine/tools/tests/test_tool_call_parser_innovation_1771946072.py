import pytest
from typing import List, Tuple, Dict

def extract_and_validate(text: str) -> Tuple[List[Tuple[str, Dict]], List[str]]:
    """
    Extract tool calls and validate them
    
    Returns:
        (valid_calls, errors)
    """
    calls = ToolCallParser.parse(text)
    valid_calls = []
    errors = []
    
    for tool_name, args in calls:
        # Basic validation
        if not tool_name or not isinstance(tool_name, str):
            errors.append(f"Invalid tool name: {tool_name}")
            continue
        
        if not isinstance(args, dict):
            errors.append(f"Invalid args for {tool_name}: {args}")
            continue
        
        valid_calls.append((tool_name, args))
    
    return valid_calls, errors

class TestToolCallParser:

    def test_happy_path(self):
        text = 'tool1({"key": "value"}) tool2({"another_key": 123})'
        expected_valid_calls = [('tool1', {'key': 'value'}), ('tool2', {'another_key': 123})]
        expected_errors = []
        valid_calls, errors = extract_and_validate(text)
        assert valid_calls == expected_valid_calls
        assert errors == expected_errors

    def test_empty_input(self):
        text = ''
        expected_valid_calls = []
        expected_errors = ['Invalid tool name: None', 'Invalid args for None: None']
        valid_calls, errors = extract_and_validate(text)
        assert valid_calls == expected_valid_calls
        assert errors == expected_errors

    def test_none_input(self):
        text = None
        expected_valid_calls = []
        expected_errors = ['Invalid tool name: None', 'Invalid args for None: None']
        valid_calls, errors = extract_and_validate(text)
        assert valid_calls == expected_valid_calls
        assert errors == expected_errors

    def test_boundary_case(self):
        text = 'tool1({"key": "value"}) tool2({})'
        expected_valid_calls = [('tool1', {'key': 'value'}), ('tool2', {})]
        expected_errors = []
        valid_calls, errors = extract_and_validate(text)
        assert valid_calls == expected_valid_calls
        assert errors == expected_errors

    def test_invalid_tool_name(self):
        text = '123({"key": "value"}) tool2({"another_key": 123})'
        expected_valid_calls = [('tool2', {'another_key': 123})]
        expected_errors = ['Invalid tool name: 123']
        valid_calls, errors = extract_and_validate(text)
        assert valid_calls == expected_valid_calls
        assert errors == expected_errors

    def test_invalid_args(self):
        text = 'tool1("key": "value") tool2({"another_key": 123})'
        expected_valid_calls = [('tool2', {'another_key': 123})]
        expected_errors = ['Invalid args for tool1: ("key": "value")']
        valid_calls, errors = extract_and_validate(text)
        assert valid_calls == expected_valid_calls
        assert errors == expected_errors

    def test_async_behavior(self):
        # Since the function does not involve any async operations, we don't need to test it here.
        pass