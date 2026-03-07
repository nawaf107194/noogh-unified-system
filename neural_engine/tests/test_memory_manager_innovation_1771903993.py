import pytest
from pathlib import Path
from typing import Optional, Dict

class MemoryCategory:
    pass  # Assuming this is defined somewhere else in your codebase

class MemoryItem:
    pass  # Assuming this is defined somewhere else in your codebase

from neural_engine.memory_manager import MemoryManager
import logging
logger = logging.getLogger(__name__)

@pytest.fixture
def memory_manager():
    return MemoryManager()

def test_happy_path(memory_manager):
    assert memory_manager.storage_path == "./memory_storage"
    assert isinstance(memory_manager.memories, dict)
    for category in MemoryCategory:
        assert category in memory_manager.memories and isinstance(memory_manager.memories[category], dict)

def test_default_storage_path(memory_manager):
    assert memory_manager.storage_path == "./memory_storage"

def test_custom_storage_path():
    custom_path = "/tmp/custom_memory"
    manager = MemoryManager(storage_path=custom_path)
    assert manager.storage_path == custom_path
    Path(custom_path).rmdir()  # Clean up the created directory

def test_empty_storage_path(tmpdir):
    with pytest.raises(ValueError):
        MemoryManager(storage_path="")

def test_none_storage_path(memory_manager):
    memory_manager = MemoryManager(storage_path=None)
    assert memory_manager.storage_path == "./memory_storage"

def test_invalid_storage_path():
    with pytest.raises(FileNotFoundError) as exc_info:
        MemoryManager(storage_path="/nonexistent/path")
    assert "No such file or directory" in str(exc_info.value)

def mock_load_memories(self):
    self.memories[MemoryCategory.DEFAULT] = {"key": MemoryItem()}

MemoryManager._load_memories = mock_load_memories

def test_load_memories(memory_manager):
    memory_manager._load_memories()
    assert MemoryCategory.DEFAULT in memory_manager.memories
    assert "key" in memory_manager.memories[MemoryCategory.DEFAULT]