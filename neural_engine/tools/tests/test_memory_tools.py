import pytest
from unittest.mock import patch, MagicMock
from neural_engine.tools.memory_tools import get_memory_stats
from neural_engine.recall_engine import get_recall_engine

@pytest.fixture
def mock_get_recall_engine():
    with patch('neural_engine.tools.memory_tools.get_recall_engine') as mock_engine:
        mock_engine.return_value = MagicMock(
            get_collection_stats=MagicMock(return_value={
                "total_memories": 100,
                "collection_name": "test_collection"
            })
        )
        yield mock_engine

@pytest.fixture
def mock_logger_error():
    with patch('neural_engine.tools.memory_tools.logger.error') as mock_logger:
        yield mock_logger

def test_get_memory_stats_happy_path(mock_get_recall_engine):
    result = get_memory_stats()
    assert result["success"] is True
    assert result["total_memories"] == 100
    assert result["collection_name"] == "test_collection"
    assert result["summary_ar"] == "إجمالي الذكريات المخزنة: 100"

def test_get_memory_stats_empty_collection(mock_get_recall_engine):
    mock_get_recall_engine.return_value.get_collection_stats.return_value = {}
    result = get_memory_stats()
    assert result["success"] is True
    assert result["total_memories"] == 0
    assert result["collection_name"] == "unknown"
    assert result["summary_ar"] == "إجمالي الذكريات المخزنة: 0"

def test_get_memory_stats_none_collection(mock_get_recall_engine):
    mock_get_recall_engine.return_value.get_collection_stats.return_value = None
    result = get_memory_stats()
    assert result["success"] is True
    assert result["total_memories"] == 0
    assert result["collection_name"] == "unknown"
    assert result["summary_ar"] == "إجمالي الذكريات المخزنة: 0"

def test_get_memory_stats_error_case(mock_logger_error):
    with patch('neural_engine.tools.memory_tools.get_recall_engine', side_effect=Exception("Test exception")):
        result = get_memory_stats()
        assert result["success"] is False
        assert result["error"] == "Test exception"
        assert result["total_memories"] == 0
        assert result["summary_ar"] == "فشل قراءة إحصائيات الذاكرة: Test exception"
        mock_logger_error.assert_called_once_with("Failed to get memory stats: Test exception")

# No async behavior in the provided function, so no async test is necessary.