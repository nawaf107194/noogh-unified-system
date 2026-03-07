import pytest
from unittest.mock import patch, MagicMock
from chromadb.errors import NoAvailableError

# Mocking the necessary imports
chromadb = MagicMock()
embedding_functions = MagicMock()
logger = MagicMock()

# Patching the imports at the module level
@pytest.fixture(autouse=True)
def patch_imports():
    with patch.dict('sys.modules', {
        'chromadb': chromadb,
        'chromadb.errors': chromadb.errors,
        'chromadb.config': chromadb.config,
        'chromadb.client': chromadb.client,
        'chromadb.api.models.Collection': chromadb.api.models.Collection,
        'chromadb.api.types': chromadb.api.types,
        'chromadb.api.embeddings': chromadb.api.embeddings,
        'chromadb.api.models.EmbeddingFunction': chromadb.api.embeddings.EmbeddingFunction,
        'chromadb.api.models.Metadata': chromadb.api.models.Metadata,
        'chromadb.api.models.EmbeddingFunction': embedding_functions.EmbeddingFunction,
        'chromadb.api.models.Collection': chromadb.api.models.Collection,
        'chromadb.api.models.Metadata': chromadb.api.models.Metadata,
        'chromadb.api.models.EmbeddingFunction': embedding_functions.EmbeddingFunction,
        'chromadb.api.models.Collection': chromadb.api.models.Collection,
        'chromadb.api.models.Metadata': chromadb.api.models.Metadata,
        'chromadb.api.models.EmbeddingFunction': embedding_functions.EmbeddingFunction,
        'logging': logger,
    }):
        yield

class TestSemanticToolRankerInit:

    @pytest.fixture
    def ranker(self):
        from semantic_ranker import SemanticToolRanker
        return SemanticToolRanker

    def test_happy_path_with_persist_dir(self, ranker):
        # Arrange
        persist_dir = "/path/to/persist"
        chromadb.PersistentClient.return_value.get_or_create_collection.return_value = MagicMock()
        
        # Act
        ranker_instance = ranker(persist_dir=persist_dir)
        
        # Assert
        assert ranker_instance.client == chromadb.PersistentClient.return_value
        assert ranker_instance.collection.name == "noogh_tools_v2"
        assert ranker_instance.collection.metadata["description"] == "NOOGH 13-tool registry for semantic matching"

    def test_happy_path_without_persist_dir(self, ranker):
        # Arrange
        chromadb.Client.return_value.get_or_create_collection.return_value = MagicMock()
        
        # Act
        ranker_instance = ranker()
        
        # Assert
        assert ranker_instance.client == chromadb.Client.return_value
        assert ranker_instance.collection.name == "noogh_tools_v2"
        assert ranker_instance.collection.metadata["description"] == "NOOGH 13-tool registry for semantic matching"

    def test_edge_case_empty_persist_dir(self, ranker):
        # Arrange
        persist_dir = ""
        chromadb.PersistentClient.return_value.get_or_create_collection.return_value = MagicMock()
        
        # Act
        ranker_instance = ranker(persist_dir=persist_dir)
        
        # Assert
        assert ranker_instance.client == chromadb.PersistentClient.return_value
        assert ranker_instance.collection.name == "noogh_tools_v2"
        assert ranker_instance.collection.metadata["description"] == "NOOGH 13-tool registry for semantic matching"

    def test_edge_case_none_persist_dir(self, ranker):
        # Arrange
        chromadb.Client.return_value.get_or_create_collection.return_value = MagicMock()
        
        # Act
        ranker_instance = ranker(persist_dir=None)
        
        # Assert
        assert ranker_instance.client == chromadb.Client.return_value
        assert ranker_instance.collection.name == "noogh_tools_v2"
        assert ranker_instance.collection.metadata["description"] == "NOOGH 13-tool registry for semantic matching"

    def test_error_case_chromadb_not_available(self, ranker):
        # Arrange
        chromadb.Available = False
        
        # Act & Assert
        with pytest.raises(ImportError) as excinfo:
            ranker()
        assert str(excinfo.value) == "ChromaDB required. pip install chromadb"

    def test_async_behavior(self, ranker):
        # This function does not have any async behavior, so we can skip this test.
        pass