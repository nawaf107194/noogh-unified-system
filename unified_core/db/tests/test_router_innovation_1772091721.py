import pytest
from unittest.mock import patch

from unified_core.db.router import Router, PostgresManager, VectorDBManager, GraphDBManager, RoutingDecision

def test_happy_path():
    postgres = PostgresManager()
    vector_db = VectorDBManager()
    graph_db = GraphDBManager()

    router = Router(postgres=postgres, vector_db=vector_db, graph_db=graph_db)

    assert router.postgres == postgres
    assert router.vector_db == vector_db
    assert router.graph_db == graph_db
    assert router._custom_rules == []
    assert router._cache == {}
    assert router._cache_size == 1000

def test_edge_case_none():
    router = Router()

    assert router.postgres is None
    assert router.vector_db is None
    assert router.graph_db is None
    assert router._custom_rules == []
    assert router._cache == {}
    assert router._cache_size == 1000

def test_error_case_invalid_input():
    with pytest.raises(TypeError):
        Router(postgres="not a PostgresManager")
    
    with pytest.raises(TypeError):
        Router(vector_db="not a VectorDBManager")
    
    with pytest.raises(TypeError):
        Router(graph_db="not a GraphDBManager")

# Async behavior is not applicable here as the __init__ method does not contain any async operations