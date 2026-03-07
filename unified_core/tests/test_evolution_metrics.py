"""Tests for evolution_metrics — in-memory metrics collector."""
import time
import pytest
from unified_core.evolution.evolution_metrics import (
    EvolutionMetrics,
    get_metrics_collector,
    inc,
    set_gauge,
    observe,
    get_metrics,
)


class TestCounters:
    def test_increment_new_counter(self):
        m = EvolutionMetrics()
        m.inc("proposals")
        metrics = m.get_metrics()
        assert metrics["counters"]["proposals"] == 1

    def test_increment_by_value(self):
        m = EvolutionMetrics()
        m.inc("requests", 5)
        assert m.get_metrics()["counters"]["requests"] == 5

    def test_multiple_increments(self):
        m = EvolutionMetrics()
        m.inc("total")
        m.inc("total")
        m.inc("total")
        assert m.get_metrics()["counters"]["total"] == 3


class TestGauges:
    def test_set_gauge(self):
        m = EvolutionMetrics()
        m.set_gauge("cpu", 45.5)
        assert m.get_metrics()["gauges"]["cpu"] == 45.5

    def test_gauge_overwrite(self):
        m = EvolutionMetrics()
        m.set_gauge("memory", 100.0)
        m.set_gauge("memory", 200.0)
        assert m.get_metrics()["gauges"]["memory"] == 200.0


class TestHistograms:
    def test_observe_creates_histogram(self):
        m = EvolutionMetrics()
        m.observe("latency", 0.5)
        m.observe("latency", 1.0)
        m.observe("latency", 1.5)
        h = m.get_metrics()["histograms"]["latency"]
        assert h["count"] == 3
        assert h["min"] == 0.5
        assert h["max"] == 1.5
        assert h["avg"] == 1.0

    def test_histogram_max_samples(self):
        m = EvolutionMetrics()
        for i in range(150):
            m.observe("big", float(i), max_samples=100)
        h = m.get_metrics()["histograms"]["big"]
        assert h["count"] == 100  # capped

    def test_p50_calculation(self):
        m = EvolutionMetrics()
        for v in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            m.observe("values", float(v))
        h = m.get_metrics()["histograms"]["values"]
        assert h["p50"] == 5.0 or h["p50"] == 6.0  # median area


class TestReset:
    def test_reset_clears_all(self):
        m = EvolutionMetrics()
        m.inc("counter")
        m.set_gauge("gauge", 1.0)
        m.observe("hist", 1.0)
        m.reset()
        metrics = m.get_metrics()
        assert metrics["counters"] == {}
        assert metrics["gauges"] == {}
        assert metrics["histograms"] == {}


class TestUptime:
    def test_uptime_tracks(self):
        m = EvolutionMetrics()
        metrics = m.get_metrics()
        assert metrics["uptime_seconds"] >= 0


class TestSingleton:
    def test_get_metrics_collector_returns_same(self):
        a = get_metrics_collector()
        b = get_metrics_collector()
        assert a is b


class TestConvenienceFunctions:
    def test_inc_function(self):
        collector = get_metrics_collector()
        collector.reset()
        inc("test_counter")
        assert get_metrics()["counters"]["test_counter"] == 1

    def test_set_gauge_function(self):
        collector = get_metrics_collector()
        collector.reset()
        set_gauge("test_gauge", 3.14)
        assert get_metrics()["gauges"]["test_gauge"] == 3.14

    def test_observe_function(self):
        collector = get_metrics_collector()
        collector.reset()
        observe("test_hist", 42.0)
        assert get_metrics()["histograms"]["test_hist"]["count"] == 1
