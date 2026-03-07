import pytest
from typing import List, Dict, Any
from collections import Counter

class SelfAwarenessAdapter:
    def _analyze_health(self, observations: List[Dict]) -> Dict[str, Any]:
        """Analyze system health trends"""
        if not observations:
            return {
                "observations": 0,
                "avg_cpu": 0.0,
                "avg_memory": 0.0,
                "health_statuses": {}
            }
        
        # Extract metrics
        cpu_values = [o.get("payload", {}).get("cpu_percent", 0) for o in observations]
        mem_values = [o.get("payload", {}).get("memory_percent", 0) for o in observations]
        health_statuses = [o.get("payload", {}).get("health_status", "unknown") for o in observations]
        
        avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
        avg_memory = sum(mem_values) / len(mem_values) if mem_values else 0.0
        
        status_counts = Counter(health_statuses)
        
        return {
            "observations": len(observations),
            "avg_cpu": avg_cpu,
            "avg_memory": avg_memory,
            "health_statuses": dict(status_counts)
        }

@pytest.fixture
def adapter():
    return SelfAwarenessAdapter()

def test_happy_path(adapter):
    observations = [
        {"payload": {"cpu_percent": 50, "memory_percent": 30, "health_status": "ok"}},
        {"payload": {"cpu_percent": 60, "memory_percent": 40, "health_status": "critical"}}
    ]
    result = adapter._analyze_health(observations)
    assert result == {
        "observations": 2,
        "avg_cpu": 55.0,
        "avg_memory": 35.0,
        "health_statuses": {"ok": 1, "critical": 1}
    }

def test_empty_observations(adapter):
    observations = []
    result = adapter._analyze_health(observations)
    assert result == {
        "observations": 0,
        "avg_cpu": 0.0,
        "avg_memory": 0.0,
        "health_statuses": {}
    }

def test_none_input(adapter):
    observations = None
    result = adapter._analyze_health(observations)
    assert result == {
        "observations": 0,
        "avg_cpu": 0.0,
        "avg_memory": 0.0,
        "health_statuses": {}
    }

def test_invalid_inputs(adapter):
    observations = [
        {"payload": {"cpu_percent": "50", "memory_percent": 30, "health_status": "ok"}},
        {"payload": {"cpu_percent": 60, "memory_percent": "40", "health_status": "critical"}}
    ]
    result = adapter._analyze_health(observations)
    assert result == {
        "observations": 2,
        "avg_cpu": 55.0,
        "avg_memory": 35.0,
        "health_statuses": {"ok": 1, "critical": 1}
    }

def test_single_observation(adapter):
    observations = [
        {"payload": {"cpu_percent": 50, "memory_percent": 30, "health_status": "ok"}}
    ]
    result = adapter._analyze_health(observations)
    assert result == {
        "observations": 1,
        "avg_cpu": 50.0,
        "avg_memory": 30.0,
        "health_statuses": {"ok": 1}
    }

def test_all_null_values(adapter):
    observations = [
        {"payload": {"cpu_percent": None, "memory_percent": None, "health_status": None}},
        {"payload": {"cpu_percent": None, "memory_percent": None, "health_status": None}}
    ]
    result = adapter._analyze_health(observations)
    assert result == {
        "observations": 2,
        "avg_cpu": 0.0,
        "avg_memory": 0.0,
        "health_statuses": {"unknown": 2}
    }