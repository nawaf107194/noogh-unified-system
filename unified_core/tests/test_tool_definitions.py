import pytest
from unittest.mock import patch

from unified_core.tool_definitions import get_tool_definition, UNIFIED_TOOLS, LEGACY_NAME_MAP

# Happy path (normal inputs)
def test_get_tool_definition_normal():
    name = "example_tool"
    expected_result = ToolDefinition(name="example_tool", description="This is an example tool")
    UNIFIED_TOOLS[name] = expected_result
    
    result = get_tool_definition(name)
    
    assert result == expected_result
    assert result.name == "example_tool"

# Edge cases (empty, None, boundaries)
def test_get_tool_definition_empty_name():
    name = ""
    result = get_tool_definition(name)
    assert result is None

def test_get_tool_definition_none_name():
    name = None
    result = get_tool_definition(name)
    assert result is None

# Error cases (invalid inputs) - No explicit error handling in the code, so no need to cover this

# Async behavior - Not applicable as the function is synchronous