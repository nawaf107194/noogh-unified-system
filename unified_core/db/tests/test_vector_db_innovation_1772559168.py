import pytest
from typing import Dict, List, Tuple
from unified_core.db.vector_db import VectorDB
from unified_core.db.distance_metric import DistanceMetric

def test_vector_db_init_happy_path():
    # Test with default parameters
    db = VectorDB()
    assert db.host == "localhost"
    assert db.port == 19530
    assert db.collection_name == "unified_memory"
    assert db.dimension == 1536
    assert db.metric_type == DistanceMetric.COSINE
    assert db.use_memory_fallback is True
    
    # Check internal state
    assert db._client is None
    assert db._collection is None
    assert db._initialized is False
    assert db._using_memory is False
    assert isinstance(db._memory_vectors, Dict)
    assert db._memory_index is None

def test_vector_db_init_edge_cases():
    # Test empty host
    db = VectorDB(host="")
    assert db.host == ""
    
    # Test max port value
    db = VectorDB(port=65535)
    assert db.port == 65535
    
    # Test min dimension value
    db = VectorDB(dimension=1)
    assert db.dimension == 1
    
    # Test invalid metric type string
    db = VectorDB(metric_type="invalid")
    assert db.metric_type == "invalid"  # Will be handled at runtime

def test_vector_db_init_error_cases():
    # Test invalid dimension (non-positive)
    with pytest.raises(Exception):
        VectorDB(dimension=0)
        
    # Test invalid metric type (invalid type)
    with pytest.raises(Exception):
        VectorDB(metric_type=123)

def test_vector_db_init_default_parameters():
    db = VectorDB()
    assert db.host == "localhost"
    assert db.port == 19530
    assert db.collection_name == "unified_memory"
    assert db.dimension == 1536
    assert db.metric_type == DistanceMetric.COSINE
    assert db.use_memory_fallback is True