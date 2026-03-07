import pytest
from neural_engine.tools.memory_tools import get_memory_stats

@pytest.fixture
def mock_recall_engine():
    class MockRecallEngine:
        def __init__(self):
            self.stats = {
                "total_memories": 10,
                "collection_name": "test_collection"
            }
        
        def get_collection_stats(self):
            return self.stats
    
    return MockRecallEngine

def test_get_memory_stats_happy_path(mock_recall_engine, monkeypatch):
    # Mock the recall engine
    monkeypatch.setattr("neural_engine.recall_engine.get_recall_engine", lambda: mock_recall_engine())
    
    result = get_memory_stats()
    
    assert result == {
        "success": True,
        "total_memories": 10,
        "collection_name": "test_collection",
        "summary_ar": "إجمالي الذكريات المخزنة: 10"
    }

def test_get_memory_stats_edge_case_empty_stats(mock_recall_engine, monkeypatch):
    # Mock the recall engine with empty stats
    mock_recall_engine.stats = {
        "total_memories": None,
        "collection_name": ""
    }
    
    monkeypatch.setattr("neural_engine.recall_engine.get_recall_engine", lambda: mock_recall_engine())
    
    result = get_memory_stats()
    
    assert result == {
        "success": True,
        "total_memories": 0,
        "collection_name": "unknown",
        "summary_ar": "إجمالي الذكريات المخزنة: 0"
    }

def test_get_memory_stats_edge_case_none_collection(mock_recall_engine, monkeypatch):
    # Mock the recall engine with None collection name
    mock_recall_engine.stats = {
        "total_memories": 5,
        "collection_name": None
    }
    
    monkeypatch.setattr("neural_engine.recall_engine.get_recall_engine", lambda: mock_recall_engine())
    
    result = get_memory_stats()
    
    assert result == {
        "success": True,
        "total_memories": 5,
        "collection_name": "unknown",
        "summary_ar": "إجمالي الذكريات المخزنة: 5"
    }

def test_get_memory_stats_error_case_no_engine(monkeypatch):
    # Mock the recall engine to raise an exception
    monkeypatch.setattr("neural_engine.recall_engine.get_recall_engine", lambda: None)
    
    result = get_memory_stats()
    
    assert not result["success"]
    assert "error" in result["error"]
    assert result["total_memories"] == 0
    assert "فشل قراءة إحصائيات الذاكرة" in result["summary_ar"]

def test_get_memory_stats_error_case_invalid_engine(monkeypatch):
    # Mock the recall engine to raise an exception
    monkeypatch.setattr("neural_engine.recall_engine.get_recall_engine", lambda: object())
    
    result = get_memory_stats()
    
    assert not result["success"]
    assert "error" in result["error"]
    assert result["total_memories"] == 0
    assert "فشل قراءة إحصائيات الذاكرة" in result["summary_ar"]