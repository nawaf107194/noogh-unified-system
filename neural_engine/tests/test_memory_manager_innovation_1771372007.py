import pytest
from typing import Optional, List
from enum import Enum
from dataclasses import dataclass

# Mocking the necessary classes and enums for testing purposes
class MemoryCategory(Enum):
    PERSONAL = 1
    WORK = 2
    EDUCATION = 3

@dataclass
class MemoryItem:
    key: str
    value: str

class MemoryManager:
    def __init__(self):
        self.memories = {cat: {} for cat in MemoryCategory}
    
    def search(
        self,
        query: str,
        category: Optional[MemoryCategory] = None
    ) -> List[MemoryItem]:
        results = []
        categories = [category] if category else list(MemoryCategory)
        
        for cat in categories:
            for item in self.memories[cat].values():
                if (query.lower() in item.key.lower() or 
                    query.lower() in str(item.value).lower()):
                    results.append(item)
        
        return results

# Test cases
@pytest.fixture
def memory_manager():
    mm = MemoryManager()
    mm.memories[MemoryCategory.PERSONAL][1] = MemoryItem('key1', 'value1')
    mm.memories[MemoryCategory.PERSONAL][2] = MemoryItem('key2', 'value2')
    mm.memories[MemoryCategory.WORK][3] = MemoryItem('key3', 'value3')
    mm.memories[MemoryCategory.EDUCATION][4] = MemoryItem('key4', 'value4')
    return mm

def test_search_happy_path(memory_manager):
    results = memory_manager.search('key1')
    assert len(results) == 1
    assert results[0].key == 'key1'
    assert results[0].value == 'value1'

def test_search_with_category(memory_manager):
    results = memory_manager.search('key1', MemoryCategory.PERSONAL)
    assert len(results) == 1
    assert results[0].key == 'key1'
    assert results[0].value == 'value1'

def test_search_empty_query(memory_manager):
    results = memory_manager.search('')
    assert len(results) == 0

def test_search_none_query(memory_manager):
    with pytest.raises(TypeError):
        memory_manager.search(None)

def test_search_nonexistent_key(memory_manager):
    results = memory_manager.search('nonexistent')
    assert len(results) == 0

def test_search_case_insensitive(memory_manager):
    results = memory_manager.search('VALUE1')
    assert len(results) == 1
    assert results[0].key == 'key1'
    assert results[0].value == 'value1'

def test_search_invalid_category(memory_manager):
    with pytest.raises(ValueError):
        memory_manager.search('key1', 'invalid_category')

def test_search_multiple_matches(memory_manager):
    memory_manager.memories[MemoryCategory.PERSONAL][5] = MemoryItem('key5', 'value1')
    results = memory_manager.search('value1')
    assert len(results) == 2
    assert all(result.value == 'value1' for result in results)

def test_search_async_behavior(memory_manager):
    # This function does not have async behavior, so we can skip this test.
    pass