import pytest

from unified_core.config.spec_loader import is_valid_tool, load_spec

def test_is_valid_tool_happy_path():
    # Arrange
    tool_name = "example_tool"
    spec = {"tools": [tool_name]}
    with patch.object(spec_loader, "load_spec", return_value=spec):
        # Act
        result = is_valid_tool(tool_name)
        
        # Assert
        assert result is True

def test_is_valid_tool_empty_tool_name():
    # Arrange
    tool_name = ""
    
    # Act
    result = is_valid_tool(tool_name)
    
    # Assert
    assert result is False

def test_is_valid_tool_none_tool_name():
    # Arrange
    tool_name = None
    
    # Act
    result = is_valid_tool(tool_name)
    
    # Assert
    assert result is False

def test_is_valid_tool_boundary_tool_name():
    # Arrange
    tool_name = "boundary_tool"
    spec = {"tools": ["tool_a", "tool_b", "boundary_tool", "tool_c"]}
    with patch.object(spec_loader, "load_spec", return_value=spec):
        # Act
        result = is_valid_tool(tool_name)
        
        # Assert
        assert result is True

def test_is_valid_tool_invalid_tool_name():
    # Arrange
    tool_name = "non_existent_tool"
    spec = {"tools": ["tool_a", "tool_b", "tool_c"]}
    with patch.object(spec_loader, "load_spec", return_value=spec):
        # Act
        result = is_valid_tool(tool_name)
        
        # Assert
        assert result is False

def test_is_valid_tool_with_empty_spec():
    # Arrange
    tool_name = "example_tool"
    spec = {}
    with patch.object(spec_loader, "load_spec", return_value=spec):
        # Act
        result = is_valid_tool(tool_name)
        
        # Assert
        assert result is False

def test_is_valid_tool_with_no_tools_in_spec():
    # Arrange
    tool_name = "example_tool"
    spec = {"tools": []}
    with patch.object(spec_loader, "load_spec", return_value=spec):
        # Act
        result = is_valid_tool(tool_name)
        
        # Assert
        assert result is False

def test_is_valid_tool_with_invalid_input_type():
    # Arrange
    tool_name = 123
    
    # Act
    result = is_valid_tool(tool_name)
    
    # Assert
    assert result is False