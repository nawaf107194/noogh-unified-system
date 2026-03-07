import pytest
from unittest.mock import patch

class MockSentenceTransformer:
    def __init__(self, model):
        self.model = model

    @staticmethod
    def load(name):
        if name == "test-model":
            return MockSentenceTransformer("test-model")
        raise ImportError(f"Module '{name}' has no attribute 'load'")

@pytest.fixture
def pinecone_store():
    class PineconeStore:
        def __init__(self, embedding_model="test-model"):
            self._embedder = None
            self.embedding_model = embedding_model

        def embedder(self):
            if self._embedder is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    self._embedder = SentenceTransformer(self.embedding_model)
                except ImportError:
                    raise ImportError("sentence-transformers not installed")
            return self._embedder

    return PineconeStore()

def test_embedder_happy_path(pinecone_store):
    embedder_instance = pinecone_store.embedder()
    assert isinstance(embedder_instance, MockSentenceTransformer)
    assert embedder_instance.model == "test-model"

def test_embedder_edge_case_none_model(pinecone_store):
    pinecone_store.embedding_model = None
    with pytest.raises(ImportError) as exc_info:
        pinecone_store.embedder()
    assert "sentence-transformers not installed" in str(exc_info.value)

@patch("sentence_transformers.SentenceTransformer.load", side_effect=ImportError("Module 'sentence_transformers' has no attribute 'load"))
def test_embedder_error_case_invalid_model(pinecone_store, mock_load):
    with pytest.raises(ImportError) as exc_info:
        pinecone_store.embedder()
    assert "Module 'sentence_transformers' has no attribute 'load'" in str(exc_info.value)