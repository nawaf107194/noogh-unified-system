import pytest
from gateway.app.core.protocol import _extract_ast_tool_call, ParsedResponse
import ast

def test_extract_ast_tool_call_happy_path():
    parsed_response = ParsedResponse(act="print('Hello')")
    result = _extract_ast_tool_call(parsed_response)
    assert result == {"tool": "print", "args": {"arg0": "'Hello'"}, "code": None, "metadata": {"toolcall": True}}

def test_extract_ast_tool_call_empty_content():
    parsed_response = ParsedResponse(act="")
    result = _extract_ast_tool_call(parsed_response)
    assert result == {"tool": "none", "args": {}, "code": None, "metadata": {}}

def test_extract_ast_tool_call_none_content():
    parsed_response = ParsedResponse(content=None)
    result = _extract_ast_tool_call(parsed_response)
    assert result == {"tool": "none", "args": {}, "code": None, "metadata": {}}

def test_extract_ast_tool_call_upper_none():
    parsed_response = ParsedResponse(act="NONE")
    result = _extract_ast_tool_call(parsed_response)
    assert result == {"tool": "none", "args": {}, "code": None, "metadata": {}}

def test_extract_ast_tool_call_invalid_syntax():
    parsed_response = ParsedResponse(act="print('Hello')!")
    result = _extract_ast_tool_call(parsed_response)
    assert result == {"tool": "none", "args": {}, "code": None, "metadata": {}}

def test_extract_ast_tool_call_positional_args():
    parsed_response = ParsedResponse(act="add(1, 2)")
    result = _extract_ast_tool_call(parsed_response)
    assert result == {"tool": "add", "args": {"arg0": 1, "arg1": 2}, "code": None, "metadata": {"toolcall": True}}

def test_extract_ast_tool_call_keyword_args():
    parsed_response = ParsedResponse(act="add(x=1, y=2)")
    result = _extract_ast_tool_call(parsed_response)
    assert result == {"tool": "add", "args": {"x": 1, "y": 2}, "code": None, "metadata": {"toolcall": True}}

def test_extract_ast_tool_call_mixed_args():
    parsed_response = ParsedResponse(act="concat('Hello', 'World')")
    result = _extract_ast_tool_call(parsed_response)
    assert result == {"tool": "concat", "args": {"arg0": "'Hello'", "arg1": "'World'"}, "code": None, "metadata": {"toolcall": True}}

def test_extract_ast_tool_call_protocol_violation():
    parsed_response = ParsedResponse(act="print('Error')", violations=["NoAccess"])
    result = _extract_ast_tool_call(parsed_response)
    assert result == {
        "tool": "reject",
        "args": {},
        "code": None,
        "metadata": {"reason": "NoAccess", "violations": ["NoAccess"]},
    }