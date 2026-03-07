"""
Unit tests for P0.3 Memory Isolation.
Tests session-based memory separation and access control.
"""
import pytest
import asyncio
from neural_engine.memory_consolidator import MemoryConsolidator
from gateway.app.core.memory_session_store import MemorySessionStore


class TestMemoryIsolation:
    """Test suite for P0.3 memory isolation."""
    
    @pytest.fixture
    def temp_db_path(self, tmp_path):
        """Create temporary ChromaDB path."""
        return str(tmp_path / "test_chroma")
    
    @pytest.fixture
    def memory(self, temp_db_path):
        """Create MemoryConsolidator instance."""
        return MemoryConsolidator(base_dir=temp_db_path, use_gpu=False)
    
    @pytest.fixture
    def session_store(self):
        """Create MemorySessionStore instance."""
        return MemorySessionStore()
    
    def test_session_creation(self, session_store):
        """Test that sessions are created with unique IDs."""
        session1 = session_store.create_session("token_1", "service")
        session2 = session_store.create_session("token_2", "service")
        
        assert session1 != session2
        assert len(session1) >= 32  # Cryptographically random
    
    def test_session_validation(self, session_store):
        """Test session validation with token matching."""
        token = "test-token-123"
        session_id = session_store.create_session(token, "admin")
        
        # Valid token should pass
        assert session_store.validate_session(session_id, token) is True
        
        # Wrong token should fail
        assert session_store.validate_session(session_id, "wrong-token") is False
        
        # Non-existent session should fail
        assert session_store.validate_session("fake-session", token) is False
    
    @pytest.mark.asyncio
    async def test_memory_isolation_basic(self, memory):
        """Test that memories from different sessions are isolated."""
        # User A stores a memory
        memory.store_memory(
            "User A secret data",
            metadata={},
            session_id="session_a",
            user_scope="service"
        )
        
        # User B should NOT recall it
        results = await memory.recall(
            "secret data",
            session_id="session_b",
            user_scope="service"
        )
        
        assert len(results) == 0, "User B should not see User A memories"
    
    @pytest.mark.asyncio
    async def test_memory_isolation_same_session(self, memory):
        """Test that memories within the same session are accessible."""
        session_id = "test_session_1"
        
        # Store memory
        memory.store_memory(
            "Secret project data",
            metadata={},
            session_id=session_id,
            user_scope="service"
        )
        
        # Same session CAN recall it
        results = await memory.recall(
            "project data",
            session_id=session_id,
            user_scope="service"
        )
        
        assert len(results) > 0, "Same session should recall its own memories"
        assert "Secret project data" in results[0]["content"]
    
    def test_session_expiration(self, session_store):
        """Test that expired sessions are cleaned up."""
        import time
        
        # Create session with 0 TTL (immediate expiration)
        token = "test-token"
        session_id = session_store.create_session(token, "service", ttl_hours=0)
        
        # Immediately should still be valid
        assert session_store.validate_session(session_id, token) is True
        
        # Wait a bit and cleanup
        time.sleep(0.1)
        cleaned = session_store.cleanup_expired()
        
        # Now should be invalid
        assert session_store.validate_session(session_id, token) is False
        assert cleaned >= 1
    
    def test_memory_count_tracking(self, session_store):
        """Test that memory operations are tracked per session."""
        token = "test-token"
        session_id = session_store.create_session(token, "service")
        
        # Initial count should be 0
        assert session_store.sessions[session_id]["memory_count"] == 0
        
        # Increment
        session_store.increment_memory_count(session_id)
        session_store.increment_memory_count(session_id)
        
        assert session_store.sessions[session_id]["memory_count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
