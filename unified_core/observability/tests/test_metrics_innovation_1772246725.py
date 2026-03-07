import pytest
from typing import Optional, Dict

class Metrics:
    def __init__(self):
        self._gauges = {}
        self._lock = threading.Lock()

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        if labels is None:
            return name
        label_str = ','.join([f'{k}={v}' for k, v in labels.items()])
        return f'{name}[{label_str}]'

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set gauge to specific value"""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value

def test_set_gauge_happy_path():
    metrics = Metrics()
    metrics.set_gauge('temperature', 23.5)
    assert metrics._gauges['temperature'] == 23.5

def test_set_gauge_with_labels():
    metrics = Metrics()
    metrics.set_gauge('volume', 100, labels={'unit': 'L'})
    assert metrics._gauges['volume[unit=L]'] == 100

def test_set_gauge_empty_label():
    metrics = Metrics()
    metrics.set_gauge('humidity', 45.2, labels={})
    assert metrics._gauges['humidity'] == 45.2

def test_set_gauge_none_label():
    metrics = Metrics()
    metrics.set_gauge('pressure', 1013.25, labels=None)
    assert metrics._gauges['pressure'] == 1013.25

def test_set_gauge_boundary_values():
    metrics = Metrics()
    metrics.set_gauge('max_speed', 340.3)
    assert metrics._gauges['max_speed'] == 340.3

def test_set_gauge_negative_value():
    metrics = Metrics()
    metrics.set_gauge('temperature', -10.2)
    assert metrics._gauges['temperature'] == -10.2

def test_set_gauge_zero_value():
    metrics = Metrics()
    metrics.set_gauge('battery_level', 0.0)
    assert metrics._gauges['battery_level'] == 0.0