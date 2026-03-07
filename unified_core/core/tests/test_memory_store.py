import pytest
from unittest.mock import patch, MagicMock
from contextlib import closing

class MockConnection:
    def __init__(self):
        self.execute_called = False

    def execute(self, query, params):
        self.execute_called = True
        assert query.startswith("INSERT INTO experiences")
        assert len(params) == 5
        return None

class TestMemoryStore:
    @patch('your_module.memory_store._get_connection', return_value=MockConnection())
    def test_record_experience_sync_happy_path(self, mock_get_connection):
        store = MemoryStore()
        store._record_experience_sync("123", "test_context", "test_action", "test_outcome", True)
        assert mock_get_connection.return_value.execute_called

    @patch('your_module.memory_store._get_connection', return_value=MockConnection())
    def test_record_experience_sync_empty_values(self, mock_get_connection):
        store = MemoryStore()
        store._record_experience_sync("", "", "", "", False)
        assert mock_get_connection.return_value.execute_called

    @patch('your_module.memory_store._get_connection', return_value=MockConnection())
    def test_record_experience_sync_none_values(self, mock_get_connection):
        store = MemoryStore()
        store._record_experience_sync(None, None, None, None, False)
        assert mock_get_connection.return_value.execute_called

    @patch('your_module.memory_store._get_connection', return_value=None)
    def test_record_experience_sync_invalid_input(self, mock_get_connection):
        store = MemoryStore()
        result = store._record_experience_sync("123", "test_context", "test_action", "test_outcome", True)
        assert result is None

    @patch('your_module.memory_store.closing')
    def test_record_experience_sync_async_behavior(self, mock_closing):
        mock_connection = MockConnection()
        with patch.object(MemoryStore, '_get_connection', return_value=mock_connection) as mock_get_conn:
            store = MemoryStore()
            result = store._record_experience_sync("123", "test_context", "test_action", "test_outcome", True)
            assert mock_closing.call_count == 1
            assert mock_connection.execute_called

if __name__ == "__main__":
    pytest.main()