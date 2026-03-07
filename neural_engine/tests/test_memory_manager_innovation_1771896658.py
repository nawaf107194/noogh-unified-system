import pytest
from neural_engine.memory_manager import MemoryCategory, MemoryManager

@pytest.fixture
def memory_manager():
    return MemoryManager()

def test_get_all_summaries_happy_path(memory_manager):
    # Arrange
    categories = [MemoryCategory.CATEGORY1, MemoryCategory.CATEGORY2]
    summaries = {cat.value: f"Summary for {cat.value}" for cat in categories}
    
    # Mock the get_category_summary method
    memory_manager.get_category_summary = lambda cat: summaries[cat.value]
    
    # Act
    result = memory_manager.get_all_summaries()
    
    # Assert
    assert result == summaries

def test_get_all_summaries_empty_categories(memory_manager):
    # Arrange
    categories = []
    
    # Mock the get_category_summary method
    memory_manager.get_category_summary = lambda cat: f"Summary for {cat.value}"
    
    # Act
    result = memory_manager.get_all_summaries()
    
    # Assert
    assert result == {}

def test_get_all_summaries_none_categories(memory_manager):
    # Arrange
    categories = None
    
    # Mock the get_category_summary method
    memory_manager.get_category_summary = lambda cat: f"Summary for {cat.value}"
    
    # Act
    result = memory_manager.get_all_summaries()
    
    # Assert
    assert result == {}

def test_get_all_summaries_invalid_input(memory_manager):
    # Arrange
    categories = "invalid input"
    
    # Mock the get_category_summary method
    memory_manager.get_category_summary = lambda cat: f"Summary for {cat.value}"
    
    # Act
    result = memory_manager.get_all_summaries()
    
    # Assert
    assert result == {}