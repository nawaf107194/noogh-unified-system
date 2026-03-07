import pytest
from unittest.mock import MagicMock, patch

class TestPineconeStore:
    @pytest.fixture
    def pinecone_store(self):
        # Mock the Pinecone index object
        mock_index = MagicMock()
        pinecone_store = PineconeStore(mock_index)
        return pinecone_store

    def test_upsert_tools_happy_path(self, pinecone_store):
        tools = {
            "tool1": {"category": "cat1", "description": "desc1"},
            "tool2": {"category": "cat2", "description": "desc2"}
        }
        embeddings = {
            "tool1": [0.1, 0.2, 0.3],
            "tool2": [0.4, 0.5, 0.6]
        }
        result = pinecone_store.upsert_tools(tools, embeddings)
        assert result == 2
        pinecone_store.index.upsert.assert_called_once()

    def test_upsert_tools_empty_inputs(self, pinecone_store):
        tools = {}
        embeddings = {}
        result = pinecone_store.upsert_tools(tools, embeddings)
        assert result == 0
        pinecone_store.index.upsert.assert_not_called()

    def test_upsert_tools_none_inputs(self, pinecone_store):
        tools = None
        embeddings = None
        with pytest.raises(TypeError):
            pinecone_store.upsert_tools(tools, embeddings)

    def test_upsert_tools_missing_embedding(self, pinecone_store):
        tools = {
            "tool1": {"category": "cat1", "description": "desc1"},
            "tool2": {"category": "cat2", "description": "desc2"}
        }
        embeddings = {
            "tool1": [0.1, 0.2, 0.3]
        }
        result = pinecone_store.upsert_tools(tools, embeddings)
        assert result == 1
        pinecone_store.index.upsert.assert_called_once()

    def test_upsert_tools_invalid_embeddings_type(self, pinecone_store):
        tools = {
            "tool1": {"category": "cat1", "description": "desc1"}
        }
        embeddings = {
            "tool1": "not a list"
        }
        with pytest.raises(TypeError):
            pinecone_store.upsert_tools(tools, embeddings)

    def test_upsert_tools_invalid_tool_definitions_type(self, pinecone_store):
        tools = {
            "tool1": "not a dictionary"
        }
        embeddings = {
            "tool1": [0.1, 0.2, 0.3]
        }
        with pytest.raises(AttributeError):
            pinecone_store.upsert_tools(tools, embeddings)

    def test_upsert_tools_async_behavior(self, pinecone_store):
        # Assuming `index.upsert` is synchronous, no async behavior to test
        pass

class PineconeStore:
    def __init__(self, index):
        self.index = index

    def upsert_tools(
        self,
        tools: Dict[str, Any],
        embeddings: Dict[str, List[float]],
    ) -> int:
        vectors = []
        for tool_name, tool_def in tools.items():
            if tool_name in embeddings:
                vectors.append({
                    "id": tool_name,
                    "values": embeddings[tool_name],
                    "metadata": {
                        "category": tool_def.get("category", ""),
                        "description": tool_def.get("description", ""),
                    },
                })
        
        if vectors:
            self.index.upsert(vectors=vectors)
        
        return len(vectors)