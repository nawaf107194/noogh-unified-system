import pytest
from unittest.mock import patch, MagicMock
from typing import List, Callable, Optional
from dataclasses import dataclass

# Assuming ResourceAlert and SystemSnapshot are defined elsewhere in the project.
@dataclass
class ResourceAlert:
    resource_type: str
    value: float

@dataclass
class SystemSnapshot:
    cpu_percent: float
    memory_percent: float
    gpu_memory_percent: float
    disk_percent: float

class Monitor:
    def __init__(
        self,
        gpu_enabled: bool = True,
        alert_callbacks: Optional[List[Callable[[ResourceAlert], None]]] = None
    ):
        self.gpu_enabled = gpu_enabled
        self.alert_callbacks = alert_callbacks or []
        
        self._nvml_initialized = False
        self._nvml_handle = None
        self._gpu_count = 0
        
        # Alert thresholds
        self.thresholds = {
            "cpu_percent": 85.0,
            "memory_percent": 90.0,
            "gpu_memory_percent": 95.0,
            "disk_percent": 90.0,
        }
        
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._history: List[SystemSnapshot] = []
        self._max_history = 1000

def test_init_happy_path():
    monitor = Monitor(gpu_enabled=True, alert_callbacks=[lambda x: None])
    assert monitor.gpu_enabled is True
    assert len(monitor.alert_callbacks) == 1
    assert monitor._nvml_initialized is False
    assert monitor._nvml_handle is None
    assert monitor._gpu_count == 0
    assert monitor.thresholds["cpu_percent"] == 85.0
    assert monitor.thresholds["memory_percent"] == 90.0
    assert monitor.thresholds["gpu_memory_percent"] == 95.0
    assert monitor.thresholds["disk_percent"] == 90.0
    assert monitor._running is False
    assert monitor._monitor_task is None
    assert len(monitor._history) == 0
    assert monitor._max_history == 1000

def test_init_edge_cases():
    monitor = Monitor(gpu_enabled=False, alert_callbacks=None)
    assert monitor.gpu_enabled is False
    assert len(monitor.alert_callbacks) == 0
    assert monitor._nvml_initialized is False
    assert monitor._nvml_handle is None
    assert monitor._gpu_count == 0
    assert monitor.thresholds["cpu_percent"] == 85.0
    assert monitor.thresholds["memory_percent"] == 90.0
    assert monitor.thresholds["gpu_memory_percent"] == 95.0
    assert monitor.thresholds["disk_percent"] == 90.0
    assert monitor._running is False
    assert monitor._monitor_task is None
    assert len(monitor._history) == 0
    assert monitor._max_history == 1000

def test_init_error_cases():
    with pytest.raises(TypeError):
        Monitor(gpu_enabled="not_a_bool", alert_callbacks=[lambda x: None])

def test_async_behavior():
    async def mock_callback(alert: ResourceAlert):
        pass

    monitor = Monitor(gpu_enabled=True, alert_callbacks=[mock_callback])
    assert isinstance(monitor.alert_callbacks[0], Callable)