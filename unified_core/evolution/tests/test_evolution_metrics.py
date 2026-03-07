import pytest

from unified_core.evolution.metrics import observe, get_metrics_collector

class MockMetricsCollector:
    def __init__(self):
        self.observations = {}

    def observe(self, name: str, value: float):
        if name not in self.observations:
            self.observations[name] = []
        self.observations[name].append(value)

@pytest.fixture
def metrics_collector():
    return MockMetricsCollector()

class TestObserve:
    @pytest.mark.usefixtures('metrics_collector')
    def test_happy_path(self, metrics_collector):
        observe("test_metric", 1.0)
        assert "test_metric" in metrics_collector.observations
        assert metrics_collector.observations["test_metric"] == [1.0]

    @pytest.mark.usefixtures('metrics_collector')
    def test_boundary_value(self, metrics_collector):
        observe("boundary_metric", 0.0)
        observe("boundary_metric", 1.0)
        assert "boundary_metric" in metrics_collector.observations
        assert metrics_collector.observations["boundary_metric"] == [0.0, 1.0]

    @pytest.mark.usefixtures('metrics_collector')
    def test_non_string_name(self, metrics_collector):
        observe(123, 1.0)
        assert "123" in metrics_collector.observations
        assert metrics_collector.observations["123"] == [1.0]

    @pytest.mark.usefixtures('metrics_collector')
    def test_non_numeric_value(self, metrics_collector):
        observe("non_numeric_metric", "string")
        assert "non_numeric_metric" in metrics_collector.observations
        assert metrics_collector.observations["non_numeric_metric"] == ["string"]

    @pytest.mark.usefixtures('metrics_collector')
    def test_empty_name(self, metrics_collector):
        observe("", 1.0)
        assert "" not in metrics_collector.observations

    @pytest.mark.usefixtures('metrics_collector')
    def test_none_value(self, metrics_collector):
        observe("none_metric", None)
        assert "none_metric" in metrics_collector.observations
        assert metrics_collector.observations["none_metric"] == [None]

    @pytest.mark.usefixtures('metrics_collector')
    def test_get_metrics_collector_mock(self, monkeypatch):
        mock_collector = MockMetricsCollector()
        monkeypatch.setattr("unified_core.evolution.metrics.get_metrics_collector", lambda: mock_collector)
        observe("mock_metric", 1.0)
        assert "mock_metric" in mock_collector.observations
        assert mock_collector.observations["mock_metric"] == [1.0]