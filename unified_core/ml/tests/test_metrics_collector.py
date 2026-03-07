import pytest
from unittest.mock import patch, MagicMock
import time

from unified_core.ml.metrics_collector import collect_metrics, SystemMetrics

PSUTIL_AVAILABLE = True  # Mocking psutil availability for testing

@pytest.mark.parametrize("mock_psutil", [
    {
        "cpu_percent": 50.0,
        "memory_percent": 75.0,
        "disk_percent": 60.0,
        "network_bytes_sent": 1024,
        "network_bytes_recv": 2048,
        "active_processes": 5
    }
], indirect=["mock_psutil"])
def test_collect_metrics_happy_path(mock_psutil):
    metrics = collect_metrics()
    assert isinstance(metrics, SystemMetrics)
    assert metrics.timestamp > 0
    assert metrics.cpu_percent == mock_psutil["cpu_percent"]
    assert metrics.memory_percent == mock_psutil["memory_percent"]
    assert metrics.disk_percent == mock_psutil["disk_percent"]
    assert metrics.network_bytes_sent == mock_psutil["network_bytes_sent"]
    assert metrics.network_bytes_recv == mock_psutil["network_bytes_recv"]
    assert metrics.active_processes == mock_psutil["active_processes"]

@patch('unified_core.ml.metrics_collector(psutil.cpu_percent)', return_value=50.0)
@patch('unified_core.ml.metrics_collector(psutil.virtual_memory)', return_value=MagicMock(percent=75.0))
@patch('unified_core.ml.metrics_collector(psutil.disk_usage)', return_value=MagicMock(percent=60.0))
@patch('unified_core.ml.metrics_collector(psutil.net_io_counters)', return_value=MagicMock(bytes_sent=1024, bytes_recv=2048))
def test_collect_metrics_edge_cases(mock_disk, mock_net, mock_memory, mock_cpu):
    metrics = collect_metrics()
    assert isinstance(metrics, SystemMetrics)
    assert metrics.timestamp > 0
    assert metrics.cpu_percent == 50.0
    assert metrics.memory_percent == 75.0
    assert metrics.disk_percent == 60.0
    assert metrics.network_bytes_sent == 1024
    assert metrics.network_bytes_recv == 2048

def test_collect_metrics_error_case_psutil_not_available():
    with patch('unified_core.ml.metrics_collector.psutil', None) as mock_psutil:
        with pytest.raises(RuntimeError):
            collect_metrics()

@patch('unified_core.ml.metrics_collector.subprocess.run')
def test_collect_metrics_async_behavior(mock_subprocess):
    mock_subprocess.return_value = MagicMock(
        stdout="0.5,40.0,1024,2048",
        returncode=0
    )
    metrics = collect_metrics()
    assert isinstance(metrics, SystemMetrics)
    assert metrics.gpu_percent == 0.5
    assert metrics.gpu_temp == 40.0
    assert metrics.gpu_memory_used == 1024.0
    assert metrics.gpu_memory_total == 2048.0