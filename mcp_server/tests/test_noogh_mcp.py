import pytest
from unittest.mock import patch, MagicMock
import json

# Mocking the external functions used in the search function
@patch('noogh_mcp.get_store')
@patch('noogh_mcp.logger')
def test_search_happy_path(mock_logger, mock_get_store):
    # Arrange
    mock_store = MagicMock()
    mock_get_store.return_value = mock_store
    mock_matches = [
        {"tool_name": "tool1", "similarity": 0.8},
        {"tool_name": "tool2", "similarity": 0.7}
    ]
    mock_store.match.return_value = mock_matches
    
    # Act
    result = search("query")
    
    # Assert
    expected_result = {
        "results": [
            {"id": "tool-tool1", "title": "tool1 (0.80)", "url": "https://noogh/tools/tool1"},
            {"id": "tool-tool2", "title": "tool2 (0.70)", "url": "https://noogh/tools/tool2"}
        ]
    }
    assert json.loads(result) == expected_result

@patch('noogh_mcp.get_store')
@patch('noogh_mcp.logger')
def test_search_empty_query(mock_logger, mock_get_store):
    # Arrange
    mock_store = MagicMock()
    mock_get_store.return_value = mock_store
    mock_store.match.return_value = []
    
    # Act
    result = search("")
    
    # Assert
    expected_result = {"results": []}
    assert json.loads(result) == expected_result

@patch('noogh_mcp.get_store')
@patch('noogh_mcp.logger')
def test_search_none_query(mock_logger, mock_get_store):
    # Arrange
    mock_store = MagicMock()
    mock_get_store.return_value = mock_store
    mock_store.match.return_value = []
    
    # Act
    result = search(None)
    
    # Assert
    expected_result = {"results": []}
    assert json.loads(result) == expected_result

@patch('noogh_mcp.get_store')
@patch('noogh_mcp.logger')
def test_search_error_case(mock_logger, mock_get_store):
    # Arrange
    mock_store = MagicMock()
    mock_get_store.return_value = mock_store
    mock_store.match.side_effect = ValueError("Invalid query")
    
    # Act
    result = search("invalid_query")
    
    # Assert
    expected_result = {"results": [], "error": "Invalid query"}
    assert json.loads(result) == expected_result

@patch('noogh_mcp.get_store')
@patch('noogh_mcp.logger')
def test_search_boundary_cases(mock_logger, mock_get_store):
    # Arrange
    mock_store = MagicMock()
    mock_get_store.return_value = mock_store
    mock_matches = [
        {"tool_name": "tool1", "similarity": 0.999},
        {"tool_name": "tool2", "similarity": 0.001}
    ]
    mock_store.match.return_value = mock_matches
    
    # Act
    result = search("boundary_query")
    
    # Assert
    expected_result = {
        "results": [
            {"id": "tool-tool1", "title": "tool1 (1.00)", "url": "https://noogh/tools/tool1"},
            {"id": "tool-tool2", "title": "tool2 (0.00)", "url": "https://noogh/tools/tool2"}
        ]
    }
    assert json.loads(result) == expected_result

# Assuming async behavior is not applicable for this function since it's synchronous
# If it were asynchronous, we would use asyncio and pytest-asyncio to test it