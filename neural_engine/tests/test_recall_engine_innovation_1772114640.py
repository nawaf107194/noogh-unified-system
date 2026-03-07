import pytest

from neural_engine.recall_engine import RecallEngine

@pytest.fixture
def recall_engine(mocker):
    mocker.patch.object(RecallEngine, 'collection')
    mocker.patch.object(RecallEngine, 'vector_db_path', return_value='/path/to/db')
    mocker.patch.object(RecallEngine, 'collection_name', return_value='test_collection')
    return RecallEngine()

def test_get_collection_stats_happy_path(recall_engine):
    recall_engine.collection.count.return_value = 10
    result = recall_engine.get_collection_stats()
    assert result == {
        "total_memories": 10,
        "collection_name": 'test_collection',
        "db_path": '/path/to/db',
    }

def test_get_collection_stats_empty_collection(recall_engine):
    recall_engine.collection.count.return_value = 0
    result = recall_engine.get_collection_stats()
    assert result == {
        "total_memories": 0,
        "collection_name": 'test_collection',
        "db_path": '/path/to/db',
    }

def test_get_collection_stats_error_case(recall_engine, caplog):
    recall_engine.collection.count.side_effect = Exception("Test error")
    result = recall_engine.get_collection_stats()
    assert not result
    assert "Error in get_collection_stats: Test error" in caplog.text

def test_get_collection_stats_async_behavior(recall_engine, loop):
    async def mock_count():
        return 15

    recall_engine.collection.count.side_effect = mock_count
    result = loop.run_until_complete(recall_engine.get_collection_stats())
    assert result == {
        "total_memories": 15,
        "collection_name": 'test_collection',
        "db_path": '/path/to/db',
    }