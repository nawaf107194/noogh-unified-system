import pytest
from typing import Dict, Any
from unittest.mock import Mock

class MetricsAggregator:
    def __init__(self):
        self.metrics = {}

    def get_latest(self, metric: str) -> Any:
        if not self.metrics.get(metric):
            return None
        return self.metrics[metric][-1]

    def get_average(self, metric: str) -> float:
        if not self.metrics.get(metric):
            return 0.0
        values = self.metrics[metric]
        return sum(values) / len(values)

    def report(self) -> Dict[str, Any]:
        """Generate a report of all metrics."""
        report = {}
        for metric, values in self.metrics.items():
            report[metric] = {
                'latest': self.get_latest(metric),
                'average': self.get_average(metric),
                'count': len(values)
            }
        return report

@pytest.fixture
def aggregator():
    aggregator = MetricsAggregator()
    aggregator.metrics = {
        'cpu_usage': [75, 80, 85],
        'memory_usage': [90, 92, 94],
        'disk_space': []
    }
    return aggregator

def test_report_happy_path(aggregator):
    report = aggregator.report()
    assert report == {
        'cpu_usage': {'latest': 85, 'average': 80.0, 'count': 3},
        'memory_usage': {'latest': 94, 'average': 92.0, 'count': 3},
        'disk_space': {'latest': None, 'average': 0.0, 'count': 0}
    }

def test_report_empty_metrics():
    aggregator = MetricsAggregator()
    aggregator.metrics = {}
    report = aggregator.report()
    assert report == {}

def test_report_none_values():
    aggregator = MetricsAggregator()
    aggregator.metrics = {'none_metric': None}
    report = aggregator.report()
    assert report == {}

def test_report_invalid_input_type():
    aggregator = MetricsAggregator()
    aggregator.metrics = 'invalid_input'
    with pytest.raises(AttributeError):
        aggregator.report()

def test_report_async_behavior():
    # Since the `report` method is synchronous, there's no async behavior to test.
    # This test case is included to demonstrate that there's no async behavior.
    pass