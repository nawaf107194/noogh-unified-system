import pytest

class MockMetrics:
    def __init__(self):
        self._counters = {}
        self._lock = pytest.MagicMock()

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        # Mock implementation of _make_key
        return f"{name}:{','.join(f'{k}={v}' for k, v in (labels or {}).items())}"

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        key = self._make_key(name, labels)
        with self._lock:
            return self._counters.get(key, 0.0)

def test_get_counter_happy_path():
    metrics = MockMetrics()
    metrics._counters["test_counter:label1=value1"] = 42.0
    assert metrics.get_counter("test_counter", {"label1": "value1"}) == 42.0

def test_get_counter_no_labels():
    metrics = MockMetrics()
    metrics._counters["test_counter"] = 99.0
    assert metrics.get_counter("test_counter") == 99.0

def test_get_counter_empty_labels():
    metrics = MockMetrics()
    metrics._counters["test_counter:label1="] = 55.0
    assert metrics.get_counter("test_counter", {"label1": ""}) == 55.0

def test_get_counter_none_labels():
    metrics = MockMetrics()
    metrics._counters["test_counter:none"] = 33.0
    assert metrics.get_counter("test_counter", None) == 33.0

def test_get_counter_no_entry():
    metrics = MockMetrics()
    assert metrics.get_counter("non_existent_counter") == 0.0

def test_get_counter_with_lock():
    metrics = MockMetrics()
    with pytest.raises(NotImplementedError):
        metrics._lock.acquire()  # This is just for demonstration; you may need to mock _lock behavior differently
        metrics.get_counter("test_counter")