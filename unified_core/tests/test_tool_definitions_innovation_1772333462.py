import pytest
from typing import List, Dict, Any
from unified_core.tool_definitions import get_all_tool_schemas, UNIFIED_TOOLS

def test_get_all_tool_schemas_happy_path():
    # Arrange
    # Assuming UNIFIED_TOOLS is already populated with some tools for testing purposes
    
    # Act
    result = get_all_tool_schemas()
    
    # Assert
    assert isinstance(result, list)
    assert all(isinstance(tool_schema, dict) for tool_schema in result)

def test_get_all_tool_schemas_edge_case_empty_tools():
    # Arrange
    global UNIFIED_TOOLS
    original_tools = UNIFIED_TOOLS.copy()
    UNIFIED_TOOLS.clear()
    
    # Act
    result = get_all_tool_schemas()
    
    # Assert
    assert isinstance(result, list)
    assert len(result) == 0
    
    # Restore the original tools for subsequent tests
    UNIFIED_TOOLS.update(original_tools)

def test_get_all_tool_schemas_edge_case_none_tools():
    # Arrange
    global UNIFIED_TOOLS
    original_tools = UNIFIED_TOOLS.copy()
    UNIFIED_TOOLS = None
    
    # Act
    result = get_all_tool_schemas()
    
    # Assert
    assert result is None
    
    # Restore the original tools for subsequent tests
    UNIFIED_TOOLS = original_tools

def test_get_all_tool_schemas_edge_case_boundary_tools():
    # Arrange
    global UNIFIED_TOOLS
    original_tools = UNIFIED_TOOLS.copy()
    UNIFIED_TOOLS = {
        "tool1": mock.Mock(to_schema=lambda: {"name": "tool1"}),
        "tool2": mock.Mock(to_schema=lambda: {"name": "tool2"})
    }
    
    # Act
    result = get_all_tool_schemas()
    
    # Assert
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(tool_schema, dict) for tool_schema in result)
    assert any(schema["name"] == "tool1" for schema in result)
    assert any(schema["name"] == "tool2" for schema in result)
    
    # Restore the original tools for subsequent tests
    UNIFIED_TOOLS = original_tools

def test_get_all_tool_schemas_error_case_invalid_input():
    # Arrange and Act & Assert
    with pytest.raises(TypeError):
        get_all_tool_schemas(123)  # Assuming it doesn't accept any arguments