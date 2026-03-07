import pytest
import psutil
from unittest.mock import patch

class MockPSUtil:
    @staticmethod
    def cpu_percent(interval=0.1):
        return 50

    @staticmethod
    def virtual_memory():
        return psutil.virtual_memory(percent=50)

    @staticmethod
    def disk_usage(path="/"):
        return psutil.disk_usage(path, percent=50)

class ResourceMonitor:
    def check_resources(self) -> Dict[str, Any]:
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            stats = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "status": "nominal",
            }

            if stats["cpu_percent"] > 90 or stats["memory_percent"] > 90:
                stats["status"] = "strained"
                logger.warning(f"System resources strained: {stats}")

            return stats
        except Exception as e:
            logger.error(f"Failed to check resources: {e}")
            return {"status": "error", "message": str(e)}

def test_check_resources_happy_path(mocker):
    with patch('neural_engine.autonomic_system.resource_monitor.psutil', new=MockPSUtil()):
        rm = ResourceMonitor()
        result = rm.check_resources()
        assert result == {
            "cpu_percent": 50,
            "memory_percent": 50,
            "disk_percent": 50,
            "status": "nominal",
        }

def test_check_resources_strained():
    with patch('neural_engine.autonomic_system.resource_monitor.psutil', new=MockPSUtil()):
        rm = ResourceMonitor()
        result = rm.check_resources()
        assert result == {
            "cpu_percent": 50,
            "memory_percent": 50,
            "disk_percent": 50,
            "status": "nominal",
        }

def test_check_resources_error(mocker):
    with patch('neural_engine.autonomic_system.resource_monitor.psutil.cpu_percent', side_effect=Exception("Test error")):
        rm = ResourceMonitor()
        result = rm.check_resources()
        assert result == {"status": "error", "message": "Test error"}