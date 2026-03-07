import pytest
from collections import Counter
from typing import List, Dict, Any
from neural_engine.specialized_systems.self_awareness_adapter import SelfAwarenessAdapter

@pytest.fixture
def adapter():
    return SelfAwarenessAdapter()

def test_happy_path(adapter):
    observations = [
        {"payload": {"cpu_percent": 50, "memory_percent": 30, "health_status": "good"}},
        {"payload": {"cpu_percent": 70, "memory_percent": 20, "health_status": "good"}},
        {"payload": {"cpu_percent": 60, "memory_percent": 40, "health_status": "warning"}}
    ]
    expected_output = {
        "observations": 3,
        "avg_cpu": 60.0,
        "avg_memory": 30.0,
        "health_statuses": {"good": 2, "warning": 1}
    }
    assert adapter._analyze_health(observations) == expected_output

def test_empty_observations(adapter):
    observations = []
    expected_output = {
        "observations": 0,
        "avg_cpu": 0.0,
        "avg_memory": 0.0,
        "health_statuses": {}
    }
    assert adapter._analyze_health(observations) == expected_output

def test_none_observations(adapter):
    with pytest.raises(TypeError):
        adapter._analyze_health(None)

def test_missing_payload_keys(adapter):
    observations = [
        {"payload": {"cpu_percent": 50}},
        {"payload": {"memory_percent": 30}},
        {"payload": {"health_status": "good"}}
    ]
    expected_output = {
        "observations": 3,
        "avg_cpu": 50.0,
        "avg_memory": 30.0,
        "health_statuses": {"good": 1}
    }
    assert adapter._analyze_health(observations) == expected_output

def test_invalid_input_type(adapter):
    with pytest.raises(TypeError):
        adapter._analyze_health("not a list")

def test_mixed_valid_and_missing_payload_keys(adapter):
    observations = [
        {"payload": {"cpu_percent": 50, "memory_percent": 30, "health_status": "good"}},
        {"payload": {}},
        {"payload": {"cpu_percent": 70, "memory_percent": 20, "health_status": "good"}},
        {"payload": {"cpu_percent": 60, "memory_percent": 40, "health_status": "warning"}}
    ]
    expected_output = {
        "observations": 4,
        "avg_cpu": 60.0,
        "avg_memory": 30.0,
        "health_statuses": {"good": 2, "warning": 1}
    }
    assert adapter._analyze_health(observations) == expected_output

def test_async_behavior(adapter):
    # Since the function is synchronous and does not involve any async operations,
    # no additional tests are needed for async behavior.
    pass