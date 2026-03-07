import pytest
from unittest.mock import patch, mock_open
from typing import List
import json
from pathlib import Path

class MockPersistentMemory:
    def __init__(self):
        self.tasks_file = Path("/path/to/tasks.json")

    def _load_tasks(self) -> List[dict]:
        if not self.tasks_file.exists():
            return []
        with open(self.tasks_file, "r") as f:
            return json.load(f)

@pytest.fixture
def persistent_memory_instance():
    return MockPersistentMemory()

def test_load_tasks_happy_path(persistent_memory_instance):
    tasks_data = '[{"id": 1, "name": "Task 1"}, {"id": 2, "name": "Task 2"}]'
    with patch("builtins.open", mock_open(read_data=tasks_data)):
        tasks = persistent_memory_instance._load_tasks()
        assert len(tasks) == 2
        assert tasks[0]["id"] == 1
        assert tasks[1]["name"] == "Task 2"

def test_load_tasks_empty_file(persistent_memory_instance):
    tasks_data = '[]'
    with patch("builtins.open", mock_open(read_data=tasks_data)):
        tasks = persistent_memory_instance._load_tasks()
        assert len(tasks) == 0

def test_load_tasks_nonexistent_file(persistent_memory_instance):
    with patch.object(Path, "exists", return_value=False):
        tasks = persistent_memory_instance._load_tasks()
        assert len(tasks) == 0

def test_load_tasks_invalid_json(persistent_memory_instance):
    tasks_data = '{"id": 1, "name": "Task 1",}'
    with patch("builtins.open", mock_open(read_data=tasks_data)), pytest.raises(json.JSONDecodeError):
        persistent_memory_instance._load_tasks()

def test_load_tasks_non_dict_entries(persistent_memory_instance):
    tasks_data = '["task 1", "task 2"]'
    with patch("builtins.open", mock_open(read_data=tasks_data)):
        tasks = persistent_memory_instance._load_tasks()
        assert len(tasks) == 2
        assert all(isinstance(task, str) for task in tasks)

def test_load_tasks_mixed_types(persistent_memory_instance):
    tasks_data = '[{"id": 1, "name": "Task 1"}, "task 2"]'
    with patch("builtins.open", mock_open(read_data=tasks_data)):
        tasks = persistent_memory_instance._load_tasks()
        assert len(tasks) == 2
        assert isinstance(tasks[0], dict)
        assert isinstance(tasks[1], str)