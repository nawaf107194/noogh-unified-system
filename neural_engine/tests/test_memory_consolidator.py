import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

class MockEmbedModel:
    def encode(self, content, convert_to_tensor=True, device="cpu"):
        return [0.1] * 32

class TestMemoryConsolidatorStoreMemory:

    @pytest.fixture
    def memory_consolidator(self):
        consolidator = MagicMock()
        consolidator.embed_model = MockEmbedModel()
        consolidator.device = "cpu"
        consolidator.use_gpu = False
        consolidator.collection.add.side_effect = lambda embeddings, documents, metadatas, ids: None
        return consolidator

    def test_happy_path(self, memory_consolidator):
        content = "Test Memory Content"
        metadata = {"key": "value"}
        session_id = "test_session"
        user_scope = "admin"

        result = memory_consolidator.store_memory(content, metadata, session_id, user_scope)

        assert result is not None
        memory_id = result[:8]
        assert len(memory_id) == 8

    def test_empty_content(self, memory_consolidator):
        content = ""
        with pytest.raises(ValueError):
            memory_consolidator.store_memory(content)

    def test_none_content(self, memory_consolidator):
        content = None
        with pytest.raises(ValueError):
            memory_consolidator.store_memory(content)

    def test_boundary_content_length(self, memory_consolidator):
        content = "a" * 1024
        result = memory_consolidator.store_memory(content)
        assert result is not None

    def test_invalid_metadata_type(self, memory_consolidator):
        metadata = "not a dict"
        with pytest.raises(TypeError):
            memory_consolidator.store_memory("test content", metadata)

    def test_async_behavior(self, memory_consolidator):
        async def store_memory_async():
            await memory_consolidator.store_memory("Test Async Content")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(store_memory_async())
        finally:
            loop.close()

    def test_gpu_mode(self, memory_consolidator):
        memory_consolidator.use_gpu = True
        content = "Test GPU Memory Content"
        result = memory_consolidator.store_memory(content)
        assert result is not None

    def test_missing_session_id(self, memory_consolidator):
        session_id = None
        result = memory_consolidator.store_memory("Test No Session ID", session_id=session_id)
        assert result is not None

    def test_missing_user_scope(self, memory_consolidator):
        user_scope = None
        with pytest.raises(ValueError):
            memory_consolidator.store_memory("Test No User Scope", user_scope=user_scope)

if __name__ == "__main__":
    pytest.main()