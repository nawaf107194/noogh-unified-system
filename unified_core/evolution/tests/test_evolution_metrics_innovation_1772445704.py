import pytest
from unittest.mock import Mock

class TestEvolutionMetrics:
    def setup_method(self):
        from unified_core.evolution.evolution_metrics import EvolutionMetrics
        self.metrics = EvolutionMetrics()
        self.metrics._lock = Mock()

    @pytest.mark.parametrize("name, value, max_samples, expected_length", [
        ("test_metric", 0.5, 100, 1),
        ("test_metric", 0.3, 50, 1),
        ("test_metric", -0.2, 100, 1),
    ])
    def test_happy_path(self, name, value, max_samples, expected_length):
        self.metrics.observe(name, value, max_samples)
        assert len(self.metrics._histograms[name]) == expected_length
        assert self.metrics._lock.acquire.call_count == 1
        assert self.metrics._lock.release.call_count == 1

    def test_edge_case_none_name(self):
        with pytest.raises(TypeError) as e:
            self.metrics.observe(None, 0.5)
        assert "name" in str(e.value)

    def test_edge_case_empty_name(self):
        with pytest.raises(ValueError) as e:
            self.metrics.observe("", 0.5)
        assert "name cannot be empty" in str(e.value)

    def test_edge_case_none_value(self):
        with pytest.raises(TypeError) as e:
            self.metrics.observe("test_metric", None)
        assert "value" in str(e.value)

    def test_edge_case_invalid_max_samples(self):
        with pytest.raises(ValueError) as e:
            self.metrics.observe("test_metric", 0.5, -1)
        assert "max_samples must be a non-negative integer" in str(e.value)

    def test_max_samples_behavior(self):
        name = "test_metric"
        max_samples = 3
        values = [0.1, 0.2, 0.3, 0.4]
        for value in values:
            self.metrics.observe(name, value, max_samples)
        assert len(self.metrics._histograms[name]) == max_samples
        assert self.metrics._histograms[name] == values[-max_samples:]