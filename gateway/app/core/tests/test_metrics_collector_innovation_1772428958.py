import pytest
from gateway.app.core.metrics_collector import MetricsCollector

@pytest.fixture
def metrics_collector():
    return MetricsCollector()

def test_happy_path(metrics_collector):
    # Setup
    metrics_collector.start_time = 0
    metrics_collector.total_requests = 100
    metrics_collector.successful_requests = 95
    metrics_collector.latencies = [1, 2, 3, 4, 5] * 20

    # Act
    result = metrics_collector.get_performance_snapshot()

    # Assert
    assert result == {
        "avg_response_time_ms": 3.0,
        "requests_per_second": 100.0,
        "success_rate": 0.95,
        "error_rate": 0.05,
        "p50_latency_ms": 3.0,
        "p95_latency_ms": 4.0,
        "p99_latency_ms": 5.0
    }

def test_empty_latencies(metrics_collector):
    # Setup
    metrics_collector.start_time = 0
    metrics_collector.total_requests = 100
    metrics_collector.successful_requests = 95
    metrics_collector.latencies = []

    # Act
    result = metrics_collector.get_performance_snapshot()

    # Assert
    assert result == {
        "avg_response_time_ms": 0.0,
        "requests_per_second": 100.0,
        "success_rate": 0.95,
        "error_rate": 0.05,
        "p50_latency_ms": 0.0,
        "p95_latency_ms": 0.0,
        "p99_latency_ms": 0.0
    }

def test_no_requests(metrics_collector):
    # Setup
    metrics_collector.start_time = 0
    metrics_collector.total_requests = 0
    metrics_collector.successful_requests = 0
    metrics_collector.latencies = []

    # Act
    result = metrics_collector.get_performance_snapshot()

    # Assert
    assert result == {
        "avg_response_time_ms": 0.0,
        "requests_per_second": 0.0,
        "success_rate": 1.0,
        "error_rate": 0.0,
        "p50_latency_ms": 0.0,
        "p95_latency_ms": 0.0,
        "p99_latency_ms": 0.0
    }

def test_invalid_latencies(metrics_collector):
    # Setup
    metrics_collector.start_time = 0
    metrics_collector.total_requests = 100
    metrics_collector.successful_requests = 95
    metrics_collector.latencies = [1, "2", 3] * 20

    # Act
    result = metrics_collector.get_performance_snapshot()

    # Assert
    assert result == {
        "avg_response_time_ms": 2.0,  # Average of 1 and 3
        "requests_per_second": 100.0,
        "success_rate": 0.95,
        "error_rate": 0.05,
        "p50_latency_ms": 2.0,  # Median of 1 and 3
        "p95_latency_ms": 3.0,  # 95th percentile is still 3
        "p99_latency_ms": 3.0   # 99th percentile is still 3
    }

def test_negative_requests(metrics_collector):
    # Setup
    metrics_collector.start_time = 0
    metrics_collector.total_requests = -1
    metrics_collector.successful_requests = 5
    metrics_collector.latencies = [1, 2, 3]

    # Act
    result = metrics_collector.get_performance_snapshot()

    # Assert
    assert result == {
        "avg_response_time_ms": 2.0,
        "requests_per_second": -1.0,
        "success_rate": 0.5,
        "error_rate": 0.5,
        "p50_latency_ms": 2.0,
        "p95_latency_ms": 3.0,
        "p99_latency_ms": 3.0
    }