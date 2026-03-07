import pytest
from typing import Dict, Optional

class Metrics:
    def inc_gauge(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment gauge"""
        pass  # Mock implementation for testing purposes

    def dec_gauge(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Decrement gauge"""
        self.inc_gauge(name, -value, labels)

@pytest.fixture
def metrics():
    return Metrics()

def test_dec_gauge_happy_path(metrics):
    metrics.dec_gauge('test_metric', value=2.5)
    # Assuming inc_gauge is correctly implemented elsewhere and this assertion checks the behavior
    assert metrics.inc_gauge.call_count == 1
    assert metrics.inc_gauge.call_args_list[0] == (('test_metric', -2.5, None), {})

def test_dec_gauge_empty_name(metrics):
    metrics.dec_gauge('')
    assert metrics.inc_gauge.call_count == 1
    assert metrics.inc_gauge.call_args_list[0] == (('', -1.0, None), {})

def test_dec_gauge_none_labels(metrics):
    metrics.dec_gauge('test_metric', labels=None)
    assert metrics.inc_gauge.call_count == 1
    assert metrics.inc_gauge.call_args_list[0] == (('test_metric', -1.0, None), {})

def test_dec_gauge_boundary_value(metrics):
    metrics.dec_gauge('test_metric', value=0.0)
    assert metrics.inc_gauge.call_count == 1
    assert metrics.inc_gauge.call_args_list[0] == (('test_metric', 0.0, None), {})

# Error cases are not applicable here as the function does not explicitly raise any exceptions