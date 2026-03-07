import pytest
from unittest.mock import patch
import psutil
from home.noogh.projects.noogh_unified_system.src.agents.health_monitor_agent import _get_metrics

class TestGetMetrics:

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_happy_path(self, mock_disk_usage, mock_virtual_memory, mock_cpu_percent):
        # Arrange
        mock_cpu_percent.return_value = 50.0
        mock_virtual_memory.return_value.percent = 60.0
        mock_disk_usage.return_value.percent = 70.0

        # Act
        result = _get_metrics()

        # Assert
        assert result == {
            "cpu": 50.0,
            "ram": 60.0,
            "disk": 70.0
        }

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_edge_cases(self, mock_disk_usage, mock_virtual_memory, mock_cpu_percent):
        # Arrange
        mock_cpu_percent.return_value = 0.0
        mock_virtual_memory.return_value.percent = 100.0
        mock_disk_usage.return_value.percent = 95.0

        # Act
        result = _get_metrics()

        # Assert
        assert result == {
            "cpu": 0.0,
            "ram": 100.0,
            "disk": 95.0
        }

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_async_behavior(self, mock_disk_usage, mock_virtual_memory, mock_cpu_percent):
        # Arrange
        async def fake_psutil_method():
            return 0.0

        mock_cpu_percent.side_effect = fake_psutil_method()
        mock_virtual_memory.return_value.percent = 100.0
        mock_disk_usage.return_value.percent = 95.0

        # Act
        result = _get_metrics()

        # Assert
        assert result == {
            "cpu": 0.0,
            "ram": 100.0,
            "disk": 95.0
        }