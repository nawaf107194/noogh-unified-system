import pytest

class MetricsAggregator:
    def __init__(self):
        self.metrics = {}

    def add_metric(self, metric_name: str, value: float):
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)

    def get_average(self, metric_name: str) -> float:
        """Get the average value of a metric."""
        values = self.metrics.get(metric_name, [])
        if not values:
            return 0.0
        return sum(values) / len(values)


@pytest.fixture
def metrics_aggregator():
    return MetricsAggregator()


def test_get_average_happy_path(metrics_aggregator):
    metrics_aggregator.add_metric('test_metric', 10)
    metrics_aggregator.add_metric('test_metric', 20)
    assert metrics_aggregator.get_average('test_metric') == 15.0


def test_get_average_empty_case(metrics_aggregator):
    assert metrics_aggregator.get_average('non_existent_metric') == 0.0
    metrics_aggregator.add_metric('empty_metric', [])
    assert metrics_aggregator.get_average('empty_metric') == 0.0


def test_get_average_none_case(metrics_aggregator):
    metrics_aggregator.metrics = None
    assert metrics_aggregator.get_average('none_case_metric') == 0.0


def test_get_average_boundary_case(metrics_aggregator):
    metrics_aggregator.add_metric('boundary_metric', [1, 2, 3, 4, 5])
    assert metrics_aggregator.get_average('boundary_metric') == 3.0


# Error cases are not applicable as the function does not raise exceptions