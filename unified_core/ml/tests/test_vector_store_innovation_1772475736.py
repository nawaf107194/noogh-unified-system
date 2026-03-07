import pytest
from unittest.mock import Mock, patch
from typing import Optional

class VectorStoreMock:
    def __init__(self):
        self.match = Mock()

@pytest.fixture
def vector_store():
    return VectorStoreMock()

def test_get_best_match_happy_path(vector_store):
    # Arrange
    query = "find the nearest restaurant"
    expected_tool_name = "restaurant_finder"

    vector_store.match.return_value = [
        {"tool_name": expected_tool_name, "score": 0.4}
    ]

    # Act
    result = vector_store.get_best_match(query)

    # Assert
    assert result == expected_tool_name
    vector_store.match.assert_called_once_with(query, n_results=1, threshold=0.3)

def test_get_best_match_no_matches(vector_store):
    # Arrange
    query = "find the nearest restaurant"
    vector_store.match.return_value = []

    # Act
    result = vector_store.get_best_match(query)

    # Assert
    assert result is None
    vector_store.match.assert_called_once_with(query, n_results=1, threshold=0.3)

def test_get_best_match_empty_query(vector_store):
    # Arrange
    query = ""
    expected_tool_name = "general_search"

    vector_store.match.return_value = [
        {"tool_name": expected_tool_name, "score": 0.4}
    ]

    # Act
    result = vector_store.get_best_match(query)

    # Assert
    assert result == expected_tool_name
    vector_store.match.assert_called_once_with(query, n_results=1, threshold=0.3)

def test_get_best_match_none_query(vector_store):
    # Arrange
    query = None
    expected_tool_name = "general_search"

    vector_store.match.return_value = [
        {"tool_name": expected_tool_name, "score": 0.4}
    ]

    # Act
    result = vector_store.get_best_match(query)

    # Assert
    assert result == expected_tool_name
    vector_store.match.assert_called_once_with(query, n_results=1, threshold=0.3)

def test_get_best_match_boundary_threshold(vector_store):
    # Arrange
    query = "find the nearest restaurant"
    expected_tool_name = "restaurant_finder"

    vector_store.match.return_value = [
        {"tool_name": expected_tool_name, "score": 0.29}
    ]

    # Act
    result = vector_store.get_best_match(query, threshold=0.3)

    # Assert
    assert result is None
    vector_store.match.assert_called_once_with(query, n_results=1, threshold=0.3)