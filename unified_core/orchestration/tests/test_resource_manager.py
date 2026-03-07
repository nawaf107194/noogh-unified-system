import pytest
from unittest.mock import Mock

class ResourceManager:
    def __init__(self):
        self._gpu_tokens = {}
        self._file_locks = set()
        self._active_tasks = []

    def get_stats(self) -> Dict:
        """Get resource usage statistics"""
        return {
            "gpu_tokens": self._gpu_tokens.copy(),
            "file_locks": len(self._file_locks),
            "active_tasks": len(self._active_tasks),
            "locked_paths": list(self._file_locks)
        }

@pytest.fixture
def resource_manager():
    return ResourceManager()

def test_get_stats_happy_path(resource_manager):
    # Arrange
    resource_manager._gpu_tokens = {'a': 1, 'b': 2}
    resource_manager._file_locks.add('/path1')
    resource_manager._active_tasks.append('task1')

    # Act
    result = resource_manager.get_stats()

    # Assert
    assert result == {
        "gpu_tokens": {'a': 1, 'b': 2},
        "file_locks": 1,
        "active_tasks": 1,
        "locked_paths": ['/path1']
    }

def test_get_stats_empty(resource_manager):
    # Arrange

    # Act
    result = resource_manager.get_stats()

    # Assert
    assert result == {
        "gpu_tokens": {},
        "file_locks": 0,
        "active_tasks": 0,
        "locked_paths": []
    }

def test_get_stats_none(resource_manager):
    # Arrange
    resource_manager._gpu_tokens = None
    resource_manager._file_locks = None
    resource_manager._active_tasks = None

    # Act
    result = resource_manager.get_stats()

    # Assert
    assert result == {
        "gpu_tokens": {},
        "file_locks": 0,
        "active_tasks": 0,
        "locked_paths": []
    }

def test_get_stats_invalid_input(resource_manager):
    # Arrange
    resource_manager._gpu_tokens = {'a': 'b'}
    resource_manager._file_locks.add(123)
    resource_manager._active_tasks.append({'key': 'value'})

    # Act
    result = resource_manager.get_stats()

    # Assert
    assert result == {
        "gpu_tokens": {},
        "file_locks": 0,
        "active_tasks": 0,
        "locked_paths": []
    }