import pytest

from unified_core.tool_registry import ToolDefinition, UNIFIED_TOOLS, get_schema

def test_get_schema_happy_path():
    """Test with a valid tool name."""
    assert get_schema("example_tool") == UNIFIED_TOOLS.get("example_tool")

def test_get_schema_edge_case_empty_string():
    """Test with an empty string."""
    assert get_schema("") is None

def test_get_schema_edge_case_none():
    """Test with None."""
    assert get_schema(None) is None

def test_get_schema_error_case_invalid_input_type():
    """Test with an invalid input type (e.g., integer)."""
    with pytest.raises(TypeError):
        get_schema(123)

def test_async_behavior_not_applicable():
    """This function does not have async behavior, so no need for this test."""
    pass