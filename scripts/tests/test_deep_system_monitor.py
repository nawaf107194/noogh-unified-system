import pytest
from unittest.mock import patch
import psutil
from src.scripts.deep_system_monitor import DeepSystemMonitor

class TestDeepSystemMonitor:

    @patch('psutil.net_io_counters')
    @patch('psutil.net_connections')
    def test_happy_path(self, mock_net_connections, mock_net_io_counters):
        # Mock the return values for net_io_counters and net_connections
        mock_net_io_counters.return_value = psutil.net_io_counters()
        mock_net_connections.return_value = psutil.net_connections(kind='inet')

        # Create an instance of DeepSystemMonitor
        monitor = DeepSystemMonitor()

        # Call the function
        result = monitor.get_network_info()

        # Assertions for happy path
        assert "io_counters" in result
        assert "connections" in result

    @patch('psutil.net_io_counters')
    @patch('psutil.net_connections')
    def test_edge_cases(self, mock_net_connections, mock_net_io_counters):
        # Mock the return values for net_io_counters and net_connections
        mock_net_io_counters.return_value = psutil.net_io_counters()
        mock_net_connections.return_value = []

        # Create an instance of DeepSystemMonitor
        monitor = DeepSystemMonitor()

        # Call the function
        result = monitor.get_network_info()

        # Assertions for edge cases
        assert "io_counters" in result and result["io_counters"]
        assert "connections" in result and result["connections"]["total"] == 0

    @patch('psutil.net_io_counters')
    @patch('psutil.net_connections')
    def test_error_cases(self, mock_net_connections, mock_net_io_counters):
        # Mock the return values for net_io_counters and net_connections
        mock_net_io_counters.side_effect = psutil.Error
        mock_net_connections.return_value = []

        # Create an instance of DeepSystemMonitor
        monitor = DeepSystemMonitor()

        # Call the function
        result = monitor.get_network_info()

        # Assertions for error cases
        assert "io_counters" in result and not result["io_counters"]
        assert "connections" in result and result["connections"]["total"] == 0

    @patch('psutil.net_io_counters')
    @patch('psutil.net_connections')
    def test_async_behavior(self, mock_net_connections, mock_net_io_counters):
        # Mock the return values for net_io_counters and net_connections
        mock_net_io_counters.return_value = psutil.net_io_counters()
        mock_net_connections.return_value = psutil.net_connections(kind='inet')

        # Create an instance of DeepSystemMonitor
        monitor = DeepSystemMonitor()

        # Call the function asynchronously (simulated)
        result = monitor.get_network_info()

        # Assertions for async behavior
        assert "io_counters" in result
        assert "connections" in result