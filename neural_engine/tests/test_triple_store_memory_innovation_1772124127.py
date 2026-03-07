import pytest
from neural_engine.triple_store_memory import TripleStoreMemory
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Mocks for dependencies
class MockClient:
    def __init__(self, path):
        self.path = path
        self.collections = {}

    def get_or_create_collection(self, name, metadata):
        if name not in self.collections:
            self.collections[name] = {"metadata": metadata}
        return self.collections[name]

class MockSentenceTransformer:
    def __init__(self, model_name):
        pass

# Set up monkey patching for dependencies
@pytest.fixture(autouse=True)
def mock_dependencies(mocker):
    mocker.patch('chromadb.PersistentClient', new=MockClient)
    mocker.patch('sentence_transformers.SentenceTransformer', new=MockSentenceTransformer)

def test_happy_path():
    base_dir = "/path/to/mock/dir"
    memory_manager = TripleStoreMemory(base_dir)
    assert memory_manager.client.path == base_dir
    assert 'facts' in memory_manager.client.collections
    assert 'dreams' in memory_manager.client.collections
    assert 'hypotheses' in memory_manager.client.collections

def test_edge_case_empty_base_dir():
    with pytest.raises(ValueError) as exc_info:
        TripleStoreMemory("")
    assert str(exc_info.value) == "Base directory cannot be empty"

def test_edge_case_none_base_dir():
    with pytest.raises(ValueError) as exc_info:
        TripleStoreMemory(None)
    assert str(exc_info.value) == "Base directory cannot be None"

def test_error_case_invalid_model_name():
    class MockSentenceTransformer:
        def __init__(self, model_name):
            raise ValueError("Invalid model name")
    
    with pytest.raises(ValueError) as exc_info:
        TripleStoreMemory("/path/to/mock/dir", embed_model=MockSentenceTransformer)
    assert str(exc_info.value) == "Invalid model name"