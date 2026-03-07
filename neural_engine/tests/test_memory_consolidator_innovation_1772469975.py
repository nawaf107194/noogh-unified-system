import pytest
from unittest.mock import patch, MagicMock
from neural_engine.memory_consolidator import MemoryConsolidator

@pytest.fixture
def memory_consolidator():
    return MemoryConsolidator()

@patch('neural_engine.memory_consolidator.logger')
def test_update_metadata_happy_path(logger, memory_consolidator):
    # Arrange
    memory_id = "test_memory"
    metadata = {"key": "value"}
    
    # Act
    memory_consolidator.collection.update.return_value = None
    memory_consolidator.update_metadata(memory_id, metadata)
    
    # Assert
    memory_consolidator.collection.update.assert_called_once_with(ids=[memory_id], metadatas=[metadata])
    logger.info.assert_called_once_with(f"Updated metadata for memory {memory_id}")

@patch('neural_engine.memory_consolidator.logger')
def test_update_metadata_empty_memory_id(logger, memory_consolidator):
    # Arrange
    memory_id = ""
    metadata = {"key": "value"}
    
    # Act
    memory_consolidator.update_metadata(memory_id, metadata)
    
    # Assert
    memory_consolidator.collection.update.assert_not_called()
    logger.error.assert_called_once_with(f"Error updating memory {memory_id}: Empty memory ID")

@patch('neural_engine.memory_consolidator.logger')
def test_update_metadata_none_memory_id(logger, memory_consolidator):
    # Arrange
    memory_id = None
    metadata = {"key": "value"}
    
    # Act
    memory_consolidator.update_metadata(memory_id, metadata)
    
    # Assert
    memory_consolidator.collection.update.assert_not_called()
    logger.error.assert_called_once_with(f"Error updating memory {memory_id}: Invalid memory ID")

@patch('neural_engine.memory_consolidator.logger')
def test_update_metadata_none_metadata(logger, memory_consolidator):
    # Arrange
    memory_id = "test_memory"
    metadata = None
    
    # Act
    memory_consolidator.update_metadata(memory_id, metadata)
    
    # Assert
    memory_consolidator.collection.update.assert_not_called()
    logger.error.assert_called_once_with(f"Error updating memory {memory_id}: Invalid metadata")

@patch('neural_engine.memory_consolidator.logger')
def test_update_metadata_empty_metadata(logger, memory_consolidator):
    # Arrange
    memory_id = "test_memory"
    metadata = {}
    
    # Act
    memory_consolidator.update_metadata(memory_id, metadata)
    
    # Assert
    memory_consolidator.collection.update.assert_not_called()
    logger.error.assert_called_once_with(f"Error updating memory {memory_id}: Invalid metadata")