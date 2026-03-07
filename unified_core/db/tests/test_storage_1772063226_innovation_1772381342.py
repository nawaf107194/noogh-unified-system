import pytest
from typing import List, Dict

class Storage:
    def __init__(self, timestamp: str, memory_state: List[Dict], innovation_state: List[Dict]):
        self.timestamp = timestamp
        self.memory_state = memory_state
        self.innovation_state = innovation_state

def test_happy_path():
    storage = Storage(
        timestamp="2023-10-05T14:30:00Z",
        memory_state=[{"key": "value"}],
        innovation_state=[{"key": "innovation"}]
    )
    assert storage.timestamp == "2023-10-05T14:30:00Z"
    assert storage.memory_state == [{"key": "value"}]
    assert storage.innovation_state == [{"key": "innovation"}]

def test_edge_case_empty_inputs():
    storage = Storage(
        timestamp="",
        memory_state=[],
        innovation_state=[]
    )
    assert storage.timestamp == ""
    assert storage.memory_state == []
    assert storage.innovation_state == []

def test_edge_case_none_inputs():
    storage = Storage(
        timestamp=None,
        memory_state=None,
        innovation_state=None
    )
    assert storage.timestamp is None
    assert storage.memory_state is None
    assert storage.innovation_state is None

def test_error_case_invalid_timestamp():
    with pytest.raises(TypeError):
        Storage(
            timestamp=12345,  # Invalid type
            memory_state=[{"key": "value"}],
            innovation_state=[{"key": "innovation"}]
        )

def test_error_case_non_dict_memory_state():
    with pytest.raises(TypeError):
        Storage(
            timestamp="2023-10-05T14:30:00Z",
            memory_state=["not a dict"],  # Invalid type
            innovation_state=[{"key": "innovation"}]
        )

def test_error_case_non_dict_innovation_state():
    with pytest.raises(TypeError):
        Storage(
            timestamp="2023-10-05T14:30:00Z",
            memory_state=[{"key": "value"}],
            innovation_state=["not a dict"]  # Invalid type
        )