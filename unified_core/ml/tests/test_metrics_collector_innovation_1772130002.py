import pytest
from unittest.mock import patch, MagicMock
import sqlite3
from datetime import datetime

from unified_core.ml.metrics_collector import MetricsCollector, SystemMetrics

class MockSystemMetrics(SystemMetrics):
    def __init__(self, timestamp=None, cpu_percent=0.5, memory_percent=0.7,
                 disk_percent=0.2, gpu_percent=0.3, gpu_temp=40,
                 gpu_memory_used=1024, gpu_memory_total=2048,
                 active_processes=5, network_bytes_sent=1000,
                 network_bytes_recv=500):
        self.timestamp = timestamp if timestamp else datetime.now()
        self.cpu_percent = cpu_percent
        self.memory_percent = memory_percent
        self.disk_percent = disk_percent
        self.gpu_percent = gpu_percent
        self.gpu_temp = gpu_temp
        self.gpu_memory_used = gpu_memory_used
        self.gpu_memory_total = gpu_memory_total
        self.active_processes = active_processes
        self.network_bytes_sent = network_bytes_sent
        self.network_bytes_recv = network_bytes_recv

@pytest.fixture
def metrics_collector(tmp_path):
    db_path = tmp_path / 'test_db.db'
    return MetricsCollector(db_path)

def test_store_metrics_happy_path(metrics_collector):
    metrics = MockSystemMetrics()
    metrics_collector.store_metrics(metrics)
    conn = sqlite3.connect(metrics_collector.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM metrics")
    count = cursor.fetchone()[0]
    assert count == 1
    conn.close()

def test_store_metrics_edge_cases(metrics_collector):
    # Test with None values for each metric
    metrics = MockSystemMetrics(None, None, None, None, None, None,
                                 None, None, None, None, None)
    metrics_collector.store_metrics(metrics)
    conn = sqlite3.connect(metrics_collector.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp FROM metrics")
    timestamp = cursor.fetchone()[0]
    assert isinstance(timestamp, datetime)
    conn.close()

def test_store_metrics_invalid_input(metrics_collector):
    with pytest.raises(TypeError) as excinfo:
        metrics_collector.store_metrics('not a SystemMetrics object')
    assert "is not an instance of SystemMetrics" in str(excinfo.value)

# Async behavior is not applicable for this synchronous function