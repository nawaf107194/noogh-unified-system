import pytest
from unittest.mock import Mock
from typing import Dict, Optional

class MetricsClass:
    def __init__(self):
        self._histograms = {}
        self._lock = Mock()

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        # Simulated implementation of _make_key
        return f"{name}_{labels}" if labels else name

    def get_histogram_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        key = self._make_key(name, labels)
        with self._lock:
            values = self._histograms.get(key, [])
            
            if not values:
                return {
                    "count": 0,
                    "sum": 0.0,
                    "p50": 0.0,
                    "p95": 0.0,
                    "p99": 0.0
                }
            
            sorted_values = sorted(values)
            count = len(sorted_values)
            
            return {
                "count": count,
                "sum": sum(sorted_values),
                "p50": sorted_values[int(count * 0.50)],
                "p95": sorted_values[int(count * 0.95)],
                "p99": sorted_values[int(count * 0.99)]
            }

def test_get_histogram_stats_happy_path():
    metrics = MetricsClass()
    name = "test_metric"
    labels = {"label1": "value1"}
    values = [10, 20, 30, 40, 50]
    key = f"{name}_{labels}"
    metrics._histograms[key] = values
    
    result = metrics.get_histogram_stats(name, labels)
    
    assert result == {
        "count": 5,
        "sum": 150.0,
        "p50": 30.0,
        "p95": 45.0,
        "p99": 50.0
    }

def test_get_histogram_stats_empty_values():
    metrics = MetricsClass()
    name = "test_metric"
    labels = {"label1": "value1"}
    key = f"{name}_{labels}"
    metrics._histograms[key] = []
    
    result = metrics.get_histogram_stats(name, labels)
    
    assert result == {
        "count": 0,
        "sum": 0.0,
        "p50": 0.0,
        "p95": 0.0,
        "p99": 0.0
    }

def test_get_histogram_stats_no_labels():
    metrics = MetricsClass()
    name = "test_metric"
    values = [10, 20, 30, 40, 50]
    key = name
    metrics._histograms[key] = values
    
    result = metrics.get_histogram_stats(name)
    
    assert result == {
        "count": 5,
        "sum": 150.0,
        "p50": 30.0,
        "p95": 45.0,
        "p99": 50.0
    }

def test_get_histogram_stats_none_labels():
    metrics = MetricsClass()
    name = "test_metric"
    values = [10, 20, 30, 40, 50]
    key = f"{name}_None"
    metrics._histograms[key] = values
    
    result = metrics.get_histogram_stats(name, None)
    
    assert result == {
        "count": 5,
        "sum": 150.0,
        "p50": 30.0,
        "p95": 45.0,
        "p99": 50.0
    }

def test_get_histogram_stats_missing_key():
    metrics = MetricsClass()
    name = "test_metric"
    labels = {"label1": "value1"}
    
    result = metrics.get_histogram_stats(name, labels)
    
    assert result == {
        "count": 0,
        "sum": 0.0,
        "p50": 0.0,
        "p95": 0.0,
        "p99": 0.0
    }