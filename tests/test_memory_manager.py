"""
Tests for MemoryManager

Tests the categorized memory system.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from neural_engine.memory_manager import (
    MemoryManager,
    MemoryCategory,
    MemoryScope,
    get_memory_manager
)


class TestMemoryManager:
    """Test suite for MemoryManager"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_initialization(self, temp_storage):
        """Test manager initialization"""
        manager = MemoryManager(storage_path=temp_storage)
        
        assert manager.storage_path == temp_storage
        assert Path(temp_storage).exists()
        assert len(manager.memories) == 4  # 4 categories
    
    def test_store_user_preference(self, temp_storage):
        """Test storing user preference"""
        manager = MemoryManager(storage_path=temp_storage)
        
        item = manager.store(
            MemoryCategory.USER_PREFER,
            "language",
            "Arabic",
            MemoryScope.GLOBAL
        )
        
        assert item.key == "language"
        assert item.value == "Arabic"
        assert item.category == MemoryCategory.USER_PREFER
        assert item.scope == MemoryScope.GLOBAL
    
    def test_retrieve_memory(self, temp_storage):
        """Test retrieving memory"""
        manager = MemoryManager(storage_path=temp_storage)
        
        # Store
        manager.store(
            MemoryCategory.PROJECT_INFO,
            "stack",
            "Python/FastAPI"
        )
        
        # Retrieve
        item = manager.retrieve(MemoryCategory.PROJECT_INFO, "stack")
        
        assert item is not None
        assert item.value == "Python/FastAPI"
    
    def test_retrieve_nonexistent(self, temp_storage):
        """Test retrieving non-existent memory"""
        manager = MemoryManager(storage_path=temp_storage)
        
        item = manager.retrieve(MemoryCategory.USER_PREFER, "nonexistent")
        
        assert item is None
    
    def test_search_memories(self, temp_storage):
        """Test searching memories"""
        manager = MemoryManager(storage_path=temp_storage)
        
        manager.store(MemoryCategory.PROJECT_INFO, "stack", "Python")
        manager.store(MemoryCategory.PROJECT_INFO, "db", "PostgreSQL")
        manager.store(MemoryCategory.EXPERIENCE, "lesson1", "Use Python for ML")
        
        # Search for "python"
        results = manager.search("python")
        
        assert len(results) >= 2  # Should find at least 2
    
    def test_search_in_category(self, temp_storage):
        """Test searching in specific category"""
        manager = MemoryManager(storage_path=temp_storage)
        
        manager.store(MemoryCategory.PROJECT_INFO, "tech", "Python")
        manager.store(MemoryCategory.EXPERIENCE, "lesson", "Python is great")
        
        # Search only in PROJECT_INFO
        results = manager.search("python", category=MemoryCategory.PROJECT_INFO)
        
        assert len(results) == 1
        assert results[0].category == MemoryCategory.PROJECT_INFO
    
    def test_delete_memory(self, temp_storage):
        """Test deleting memory"""
        manager = MemoryManager(storage_path=temp_storage)
        
        manager.store(MemoryCategory.USER_PREFER, "theme", "dark")
        
        # Delete
        deleted = manager.delete(MemoryCategory.USER_PREFER, "theme")
        
        assert deleted == True
        
        # Verify deleted
        item = manager.retrieve(MemoryCategory.USER_PREFER, "theme")
        assert item is None
    
    def test_delete_nonexistent(self, temp_storage):
        """Test deleting non-existent memory"""
        manager = MemoryManager(storage_path=temp_storage)
        
        deleted = manager.delete(MemoryCategory.USER_PREFER, "nonexistent")
        
        assert deleted == False
    
    def test_category_summary(self, temp_storage):
        """Test getting category summary"""
        manager = MemoryManager(storage_path=temp_storage)
        
        manager.store(MemoryCategory.USER_PREFER, "key1", "value1")
        manager.store(MemoryCategory.USER_PREFER, "key2", "value2")
        
        summary = manager.get_category_summary(MemoryCategory.USER_PREFER)
        
        assert summary["category"] == "user_prefer"
        assert summary["count"] == 2
        assert "key1" in summary["keys"]
        assert "key2" in summary["keys"]
    
    def test_all_summaries(self, temp_storage):
        """Test getting all summaries"""
        manager = MemoryManager(storage_path=temp_storage)
        
        manager.store(MemoryCategory.USER_PREFER, "k1", "v1")
        manager.store(MemoryCategory.PROJECT_INFO, "k2", "v2")
        
        summaries = manager.get_all_summaries()
        
        assert len(summaries) == 4  # All 4 categories
        assert "user_prefer" in summaries
        assert "project_info" in summaries
    
    def test_persistence(self, temp_storage):
        """Test persistence across instances"""
        # First instance
        manager1 = MemoryManager(storage_path=temp_storage)
        manager1.store(MemoryCategory.USER_PREFER, "test", "value")
        
        # Second instance
        manager2 = MemoryManager(storage_path=temp_storage)
        item = manager2.retrieve(MemoryCategory.USER_PREFER, "test")
        
        assert item is not None
        assert item.value == "value"
    
    def test_helper_methods(self, temp_storage):
        """Test convenience helper methods"""
        manager = MemoryManager(storage_path=temp_storage)
        
        # User preference
        manager.remember_user_preference("lang", "ar")
        item = manager.retrieve(MemoryCategory.USER_PREFER, "lang")
        assert item.value == "ar"
        
        # Project info
        manager.remember_project_info("tech", "Python")
        item = manager.retrieve(MemoryCategory.PROJECT_INFO, "tech")
        assert item.value == "Python"
        
        # Lesson
        manager.remember_lesson("tip", "Always test")
        item = manager.retrieve(MemoryCategory.EXPERIENCE, "tip")
        assert item.value == "Always test"


class TestGlobalMemoryManager:
    """Test global memory manager singleton"""
    
    def test_get_global_manager(self):
        """Test getting global manager"""
        manager1 = get_memory_manager()
        manager2 = get_memory_manager()
        
        # Should be same instance
        assert manager1 is manager2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
