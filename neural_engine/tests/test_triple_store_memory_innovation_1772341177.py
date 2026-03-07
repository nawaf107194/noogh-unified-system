import pytest

from neural_engine.triple_store_memory import TripleStoreMemory

@pytest.fixture
def triple_store():
    return TripleStoreMemory()

def test_happy_path(triple_store):
    # Mock the facts and query method to return expected results
    triple_store.facts = {
        "count": lambda: 3,
        "query": lambda query_embeddings, n_results: {
            "ids": [[1, 2, 3]],
            "documents": [["doc1", "doc2", "doc3"]],
            "metadatas": [["meta1", "meta2", "meta3"]],
            "distances": [[0.1, 0.2, 0.3]]
        }
    }

    result = triple_store.recall_facts("query", n=5)
    assert len(result) == 3
    for item in result:
        assert isinstance(item["id"], int)
        assert isinstance(item["content"], str)
        assert isinstance(item["metadata"], dict)
        assert isinstance(item["distance"], float)
        assert isinstance(item["similarity"], float)

def test_empty_facts(triple_store):
    triple_store.facts = {
        "count": lambda: 0,
        "query": lambda *args, **kwargs: {}
    }

    result = triple_store.recall_facts("query", n=5)
    assert result == []

def test_none_query(triple_store):
    triple_store.facts = {
        "count": lambda: 3,
        "query": lambda query_embeddings, n_results: {
            "ids": [[1, 2, 3]],
            "documents": [["doc1", "doc2", "doc3"]],
            "metadatas": [["meta1", "meta2", "meta3"]],
            "distances": [[0.1, 0.2, 0.3]]
        }
    }

    result = triple_store.recall_facts(None, n=5)
    assert len(result) == 3

def test_boundary_n(triple_store):
    triple_store.facts = {
        "count": lambda: 3,
        "query": lambda query_embeddings, n_results: {
            "ids": [[1]],
            "documents": [["doc1"]],
            "metadatas": [["meta1"]],
            "distances": [[0.1]]
        }
    }

    result = triple_store.recall_facts("query", n=1)
    assert len(result) == 1

def test_invalid_query(triple_store):
    # Assuming the function does not raise any exceptions for invalid queries
    triple_store.facts = {
        "count": lambda: 3,
        "query": lambda query_embeddings, n_results: {}
    }

    result = triple_store.recall_facts("invalid", n=5)
    assert result == []