import pytest
from neural_engine.recall_engine import RecallEngine
import chromadb
from sentence_transformers import SentenceTransformer

@pytest.fixture
def recall_engine():
    return RecallEngine()

def test_happy_path(recall_engine):
    assert isinstance(recall_engine.client, chromadb.PersistentClient)
    assert isinstance(recall_engine.collection, chromadb.Collection)
    assert isinstance(recall_engine.embed_model, SentenceTransformer)

def test_empty_vector_db_path(recall_engine):
    with pytest.raises(RuntimeError):
        RecallEngine(vector_db_path="")

def test_none_vector_db_path(recall_engine):
    with pytest.raises(RuntimeError):
        RecallEngine(vector_db_path=None)

def test_boundary_collection_name(recall_engine):
    with pytest.raises(RuntimeError):
        RecallEngine(collection_name="")

def test_none_collection_name(recall_engine):
    with pytest.raises(RuntimeError):
        RecallEngine(collection_name=None)