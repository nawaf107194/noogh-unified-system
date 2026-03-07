import pytest
from neural_engine.memory_manager import MemoryManager
from enum import Enum

class MemoryCategory(Enum):
    EXPERIENCE = 1

class MemoryScope(Enum):
    GLOBAL = 1

@pytest.fixture
def memory_manager():
    return MemoryManager()

def test_remember_lesson_happy_path(memory_manager):
    key = "test_key"
    value = "test_value"
    result = memory_manager.remember_lesson(key, value)
    assert result is not None

def test_remember_lesson_empty_string(memory_manager):
    key = ""
    value = "test_value"
    result = memory_manager.remember_lesson(key, value)
    assert result is not None

def test_remember_lesson_none_key(memory_manager):
    key = None
    value = "test_value"
    with pytest.raises(TypeError):
        memory_manager.remember_lesson(key, value)

def test_remember_lesson_none_value(memory_manager):
    key = "test_key"
    value = None
    result = memory_manager.remember_lesson(key, value)
    assert result is not None

def test_remember_lesson_invalid_input(memory_manager):
    key = 123  # Invalid type
    value = "test_value"
    with pytest.raises(TypeError):
        memory_manager.remember_lesson(key, value)

# Assuming store method does not have async behavior, if it does, we would need to mock it and test async behavior accordingly.