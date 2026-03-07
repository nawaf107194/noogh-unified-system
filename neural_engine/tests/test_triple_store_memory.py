import pytest
from neural_engine.triple_store_memory import TripleStoreMemory

def test_store_happy_path():
    memory = TripleStoreMemory()
    content = "Test fact"
    metadata = {"source": "test"}
    assert memory.store(content, metadata) == memory.store_fact(content, source="legacy", metadata=metadata)

def test_store_empty_content():
    memory = TripleStoreMemory()
    content = ""
    metadata = None
    assert memory.store(content, metadata) is None

def test_store_none_content():
    memory = TripleStoreMemory()
    content = None
    metadata = {"source": "test"}
    assert memory.store(content, metadata) is None

def test_store_boundary_metadata():
    memory = TripleStoreMemory()
    content = "Test fact"
    metadata = {"key": "value", "another_key": 123}
    assert memory.store(content, metadata) == memory.store_fact(content, source="legacy", metadata=metadata)

def test_store_invalid_content_type():
    memory = TripleStoreMemory()
    content = 123
    metadata = None
    assert memory.store(content, metadata) is None

def test_store_invalid_metadata_type():
    memory = TripleStoreMemory()
    content = "Test fact"
    metadata = 456
    assert memory.store(content, metadata) is None