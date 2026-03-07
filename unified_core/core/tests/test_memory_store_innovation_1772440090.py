import pytest
from unittest.mock import patch, MagicMock
from contextlib import closing
from unified_core.core.memory_store import MemoryStore

class MockConnection:
    def execute(self, query, params):
        self.query = query
        self.params = params

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

@patch('unified_core.core.memory_store.closing')
def test_set_belief_sync_happy_path(mock_closing):
    # Arrange
    memory_store = MemoryStore()
    mock_connection = MockConnection()
    mock_closing.return_value.__enter__.return_value = mock_connection
    key = "test_key"
    value = {"data": 123}
    utility = 0.9

    # Act
    result = memory_store._set_belief_sync(key, value, utility)

    # Assert
    assert result is None
    assert mock_connection.query == "INSERT INTO beliefs (key, value, utility_score) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, utility_score=excluded.utility_score, updated_at=CURRENT_TIMESTAMP"
    assert mock_connection.params == (key, '{"data": 123}', utility)

@patch('unified_core.core.memory_store.closing')
def test_set_belief_sync_empty_key(mock_closing):
    # Arrange
    memory_store = MemoryStore()
    mock_connection = MockConnection()
    mock_closing.return_value.__enter__.return_value = mock_connection
    key = ""
    value = {"data": 123}
    utility = 0.9

    # Act
    result = memory_store._set_belief_sync(key, value, utility)

    # Assert
    assert result is None
    assert mock_connection.query == "INSERT INTO beliefs (key, value, utility_score) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, utility_score=excluded.utility_score, updated_at=CURRENT_TIMESTAMP"
    assert mock_connection.params == ('', '{"data": 123}', utility)

@patch('unified_core.core.memory_store.closing')
def test_set_belief_sync_none_value(mock_closing):
    # Arrange
    memory_store = MemoryStore()
    mock_connection = MockConnection()
    mock_closing.return_value.__enter__.return_value = mock_connection
    key = "test_key"
    value = None
    utility = 0.9

    # Act
    result = memory_store._set_belief_sync(key, value, utility)

    # Assert
    assert result is None
    assert mock_connection.query == "INSERT INTO beliefs (key, value, utility_score) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, utility_score=excluded.utility_score, updated_at=CURRENT_TIMESTAMP"
    assert mock_connection.params == ('test_key', None, utility)

@patch('unified_core.core.memory_store.closing')
def test_set_belief_sync_invalid_utility(mock_closing):
    # Arrange
    memory_store = MemoryStore()
    mock_connection = MockConnection()
    mock_closing.return_value.__enter__.return_value = mock_connection
    key = "test_key"
    value = {"data": 123}
    utility = -0.1

    # Act
    result = memory_store._set_belief_sync(key, value, utility)

    # Assert
    assert result is None
    assert mock_connection.query == "INSERT INTO beliefs (key, value, utility_score) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, utility_score=excluded.utility_score, updated_at=CURRENT_TIMESTAMP"
    assert mock_connection.params == ('test_key', '{"data": 123}', -0.1)

@patch('unified_core.core.memory_store.closing')
def test_set_belief_sync_error(mock_closing):
    # Arrange
    memory_store = MemoryStore()
    mock_connection = MockConnection()
    mock_closing.return_value.__enter__.return_value = mock_connection
    def execute(query, params):
        raise Exception("Database error")
    mock_connection.execute = execute

    key = "test_key"
    value = {"data": 123}
    utility = 0.9

    # Act and Assert
    with pytest.raises(Exception) as exc_info:
        memory_store._set_belief_sync(key, value, utility)
    
    assert str(exc_info.value) == "Database error"