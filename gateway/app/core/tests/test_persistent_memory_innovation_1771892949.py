import pytest
from datetime import datetime
import json
from gateway.app.core.persistent_memory import PersistentMemory

@pytest.fixture
def memory_instance(tmp_path):
    output_file = tmp_path / "memory_export.json"
    return PersistentMemory(), output_file

def test_happy_path(memory_instance, tmp_path):
    memory, output_file = memory_instance
    memory._load_tasks = lambda: ["task1", "task2"]
    memory._load_conversations = lambda: {"conv1": "message1"}
    
    memory.export_memory(output_file)
    
    with open(output_file, "r") as f:
        data = json.load(f)
    
    assert data == {
        "tasks": ["task1", "task2"],
        "conversations": {"conv1": "message1"},
        "exported_at": datetime.now().isoformat(),
    }

def test_edge_cases(memory_instance, tmp_path):
    memory, output_file = memory_instance
    memory._load_tasks = lambda: []
    memory._load_conversations = lambda: {}
    
    memory.export_memory(output_file)
    
    with open(output_file, "r") as f:
        data = json.load(f)
    
    assert data == {
        "tasks": [],
        "conversations": {},
        "exported_at": datetime.now().isoformat(),
    }

def test_error_cases(memory_instance, tmp_path):
    memory, output_file = memory_instance
    memory._load_tasks = lambda: ["task1", "task2"]
    memory._load_conversations = lambda: {"conv1": "message1"}
    
    with pytest.raises(TypeError) as exc_info:
        memory.export_memory(None)
    assert str(exc_info.value) == "output_file must be a string"

def test_async_behavior(memory_instance):
    # PersistentMemory does not have any async behavior, so this test is not applicable
    pass