import pytest
from unittest.mock import patch, MagicMock
from unified_core.system.memory_summarizer import MemorySummarizer

class MockDBConnection:
    def __init__(self):
        self.cursor = MagicMock()
    
    def commit(self):
        pass

@patch('unified_core.system.memory_summarizer.connect', return_value=MockDBConnection())
def test_setup_happy_path(mock_connect):
    summarizer = MemorySummarizer()
    summarizer.setup()
    mock_connect.return_value.cursor.execute.assert_called_once_with(
        "CREATE TABLE IF NOT EXISTS memory_summary (id INTEGER PRIMARY KEY, summary TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
    )
    mock_connect.return_value.commit.assert_called_once()

def test_setup_none_inputs():
    summarizer = MemorySummarizer(None)
    with pytest.raises(Exception) as e:
        summarizer.setup()
    assert str(e.value) == "Database connection is None"

@patch('unified_core.system.memory_summarizer.connect', side_effect=Exception("Connection failed"))
def test_setup_error_case(mock_connect):
    summarizer = MemorySummarizer()
    with pytest.raises(Exception) as e:
        summarizer.setup()
    assert str(e.value) == "Connection failed"