import pytest
from typing import Dict, Any
import statistics

class MockActuator:
    def __init__(self, latencies, tokens, capacity, blocked_count, rejection_count, cooldown_count, latency_ewma, lock_retries):
        self.latencies = latencies
        self._tokens = tokens
        self._capacity = capacity
        self.blocked_count = blocked_count
        self.rejection_count = rejection_count
        self.cooldown_count = cooldown_count
        self._latency_ewma = latency_ewma
        self.lock_retries = lock_retries

    def get_resilience_metrics(self) -> Dict[str, Any]:
        """Provides precision metrics for the Resilience Report."""
        p95 = statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) > 5 else 0
        p50 = statistics.median(self.latencies) if self.latencies else 0
        return {
            "tokens": round(self._tokens, 2),
            "capacity": self._capacity,
            "blocked": self.blocked_count,
            "rejected": self.rejection_count,
            "cooldowns": self.cooldown_count,
            "latency_ewma_ms": round(self._latency_ewma * 1000, 2),
            "p95_ms": round(p95 * 1000, 2),
            "p50_ms": round(p50 * 1000, 2),
            "lock_retries": self.lock_retries
        }

@pytest.fixture
def mock_actuator():
    return MockActuator(latencies=[10, 20, 30, 40, 50], tokens=100, capacity=1000, blocked_count=5, rejection_count=2, cooldown_count=3, latency_ewma=0.01, lock_retries=1)

def test_get_resilience_metrics_happy_path(mock_actuator):
    result = mock_actuator.get_resilience_metrics()
    assert result["tokens"] == 100.0
    assert result["capacity"] == 1000
    assert result["blocked"] == 5
    assert result["rejected"] == 2
    assert result["cooldowns"] == 3
    assert result["latency_ewma_ms"] == 10.0
    assert result["p95_ms"] == 50.0
    assert result["p50_ms"] == 30.0
    assert result["lock_retries"] == 1

def test_get_resilience_metrics_empty_latencies():
    actuator = MockActuator(latencies=[], tokens=100, capacity=1000, blocked_count=5, rejection_count=2, cooldown_count=3, latency_ewma=0.01, lock_retries=1)
    result = actuator.get_resilience_metrics()
    assert result["p95_ms"] == 0.0
    assert result["p50_ms"] == 0.0

def test_get_resilience_metrics_less_than_five_latencies():
    actuator = MockActuator(latencies=[10, 20, 30], tokens=100, capacity=1000, blocked_count=5, rejection_count=2, cooldown_count=3, latency_ewma=0.01, lock_retries=1)
    result = actuator.get_resilience_metrics()
    assert result["p95_ms"] == 0.0
    assert result["p50_ms"] == 20.0

def test_get_resilience_metrics_invalid_input():
    with pytest.raises(TypeError):
        actuator = MockActuator(latencies="not a list", tokens=100, capacity=1000, blocked_count=5, rejection_count=2, cooldown_count=3, latency_ewma=0.01, lock_retries=1)
        actuator.get_resilience_metrics()

def test_get_resilience_metrics_async_behavior():
    # Since the function is synchronous, there's no async behavior to test.
    pass