import pytest
from unittest.mock import MagicMock, patch

class PineconeStoreMock:
    def upsert_tools(self, tool_registry: Dict[str, Any], embeddings: Dict[str, Any]) -> int:
        return len(embeddings)

@pytest.fixture
def pinecone_store():
    return PineconeStoreMock()

def test_index_tools_happy_path(pinecone_store):
    store = pinecone_store
    tool_registry = {
        "tool1": {"description": "Desc1", "category": "Cat1"},
        "tool2": {"description": "Desc2", "category": "Cat2"}
    }
    
    with patch('your_module.embed', return_value=[0.1] * 768):
        result = store.index_tools(tool_registry)
    
    assert result == 2

def test_index_tools_empty_tool_registry(pinecone_store):
    store = pinecone_store
    tool_registry = {}
    
    with patch('your_module.embed', return_value=[]):
        result = store.index_tools(tool_registry)
    
    assert result == 0

def test_index_tools_none_tool_registry(pinecone_store):
    store = pinecone_store
    tool_registry = None
    
    with patch('your_module.embed', return_value=[]):
        result = store.index_tools(tool_registry)
    
    assert result is None

def test_index_tools_invalid_tool_registry(pinecone_store):
    store = pinecone_store
    tool_registry = "not_a_dict"
    
    with patch('your_module.embed', return_value=[]):
        with pytest.raises(TypeError) as exc_info:
            store.index_tools(tool_registry)
    
    assert str(exc_info.value) == "'str' object is not iterable"

def test_index_tools_async_behavior(pinecone_store, event_loop):
    store = pinecone_store
    tool_registry = {
        "tool1": {"description": "Desc1", "category": "Cat1"},
        "tool2": {"description": "Desc2", "category": "Cat2"}
    }
    
    async def mock_embed(text: str) -> List[float]:
        return [0.1] * 768
    
    with patch('your_module.embed', side_effect=mock_embed):
        result = event_loop.run_until_complete(store.index_tools(tool_registry))
    
    assert result == 2