import pytest

from unified_core.db.vector_db import VectorDB, DistanceMetric

def test_happy_path():
    db = VectorDB(
        host="localhost",
        port=19530,
        collection_name="unified_memory",
        dimension=1536,
        metric_type=DistanceMetric.COSINE,
        use_memory_fallback=True
    )
    assert db.host == "localhost"
    assert db.port == 19530
    assert db.collection_name == "unified_memory"
    assert db.dimension == 1536
    assert db.metric_type == DistanceMetric.COSINE
    assert db.use_memory_fallback is True
    assert db._client is None
    assert db._collection is None
    assert db._initialized is False
    assert db._using_memory is False
    assert db._memory_vectors == {}
    assert db._memory_index is None

def test_edge_cases():
    db = VectorDB(
        host="",
        port=0,
        collection_name=None,
        dimension=0,
        metric_type=DistanceMetric.L2,
        use_memory_fallback=False
    )
    assert db.host == ""
    assert db.port == 0
    assert db.collection_name is None
    assert db.dimension == 0
    assert db.metric_type == DistanceMetric.L2
    assert db.use_memory_fallback is False
    assert db._client is None
    assert db._collection is None
    assert db._initialized is False
    assert db._using_memory is False
    assert db._memory_vectors == {}
    assert db._memory_index is None

def test_error_cases():
    with pytest.raises(ValueError):
        VectorDB(
            host="localhost",
            port=19530,
            collection_name="unified_memory",
            dimension=-1,
            metric_type=DistanceMetric.COSINE,
            use_memory_fallback=True
        )

def test_async_behavior():
    # Assuming the class does not have async behavior, this test is irrelevant.
    pass