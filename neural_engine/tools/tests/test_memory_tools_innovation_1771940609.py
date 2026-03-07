import pytest
from unittest.mock import patch, MagicMock

# Import the function to test
from neural_engine.tools.memory_tools import get_memory_stats

def test_get_memory_stats_happy_path():
    # Mock the recall engine and its method
    with patch('neural_engine.recall_engine.get_recall_engine') as mock_get_engine:
        mock_engine = MagicMock()
        mock_engine.get_collection_stats.return_value = {
            "total_memories": 100,
            "collection_name": "test_collection"
        }
        mock_get_engine.return_value = mock_engine

        # Call the function
        result = get_memory_stats()

        # Assert the expected output
        assert result == {
            "success": True,
            "total_memories": 100,
            "collection_name": "test_collection",
            "summary_ar": "إجمالي الذكريات المخزنة: 100"
        }

def test_get_memory_stats_empty_stats():
    # Mock the recall engine and its method
    with patch('neural_engine.recall_engine.get_recall_engine') as mock_get_engine:
        mock_engine = MagicMock()
        mock_engine.get_collection_stats.return_value = {}
        mock_get_engine.return_value = mock_engine

        # Call the function
        result = get_memory_stats()

        # Assert the expected output
        assert result == {
            "success": True,
            "total_memories": 0,
            "collection_name": "unknown",
            "summary_ar": "إجمالي الذكريات المخزنة: 0"
        }

def test_get_memory_stats_error():
    # Mock the recall engine and its method
    with patch('neural_engine.recall_engine.get_recall_engine') as mock_get_engine:
        mock_engine = MagicMock()
        mock_engine.get_collection_stats.side_effect = Exception("Internal error")
        mock_get_engine.return_value = mock_engine

        # Call the function
        result = get_memory_stats()

        # Assert the expected output
        assert result == {
            "success": False,
            "error": "Internal error",
            "total_memories": 0,
            "summary_ar": "فشل قراءة إحصائيات الذاكرة: Internal error"
        }