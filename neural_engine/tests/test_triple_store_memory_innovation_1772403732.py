import pytest
from neural_engine.triple_store_memory import TripleStoreMemory
from dataclasses import asdict

def test_store_fact_happy_path():
    memory = TripleStoreMemory()
    content = "This is a factual observation."
    source = "user"
    metadata = {"confidence": 0.9}

    result = memory.store_fact(content, source, metadata)

    assert result.id
    assert result.content == content
    assert isinstance(result.timestamp, datetime.datetime)
    stored_fact = memory.facts[0]
    assert stored_fact.documents[0] == content
    assert stored_fact.metadatas[0]["source"] == source
    assert stored_fact.metadatas[0]["type"] == "fact"
    assert stored_fact.metadatas[0]["timestamp"] == pytest.approx(result.timestamp.timestamp())

def test_store_fact_empty_content():
    memory = TripleStoreMemory()
    content = ""
    source = "user"

    result = memory.store_fact(content, source)

    assert not result.id
    assert not result.content
    assert result.timestamp is None
    assert memory.facts == []

def test_store_fact_none_source():
    memory = TripleStoreMemory()
    content = "This is a factual observation."
    source = None

    result = memory.store_fact(content, source)

    assert result.id
    assert result.content == content
    assert isinstance(result.timestamp, datetime.datetime)
    stored_fact = memory.facts[0]
    assert stored_fact.documents[0] == content
    assert stored_fact.metadatas[0]["source"] is None
    assert stored_fact.metadatas[0]["type"] == "fact"
    assert stored_fact.metadatas[0]["timestamp"] == pytest.approx(result.timestamp.timestamp())

def test_store_fact_boundary_metadata():
    memory = TripleStoreMemory()
    content = "This is a factual observation."
    source = "user"
    metadata = {"confidence": 1.0}

    result = memory.store_fact(content, source, metadata)

    assert result.id
    assert result.content == content
    assert isinstance(result.timestamp, datetime.datetime)
    stored_fact = memory.facts[0]
    assert stored_fact.documents[0] == content
    assert stored_fact.metadatas[0]["source"] == source
    assert stored_fact.metadatas[0]["type"] == "fact"
    assert stored_fact.metadatas[0]["timestamp"] == pytest.approx(result.timestamp.timestamp())

def test_store_fact_invalid_metadata_type():
    memory = TripleStoreMemory()
    content = "This is a factual observation."
    source = "user"
    metadata = ["confidence", 0.9]

    result = memory.store_fact(content, source, metadata)

    assert not result.id
    assert not result.content
    assert result.timestamp is None
    assert memory.facts == []

def test_store_fact_invalid_content_type():
    memory = TripleStoreMemory()
    content = 12345
    source = "user"

    result = memory.store_fact(content, source)

    assert not result.id
    assert not result.content
    assert result.timestamp is None
    assert memory.facts == []

def test_store_fact_invalid_source_type():
    memory = TripleStoreMemory()
    content = "This is a factual observation."
    source = 12345

    result = memory.store_fact(content, source)

    assert not result.id
    assert not result.content
    assert result.timestamp is None
    assert memory.facts == []