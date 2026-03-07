import pytest

class TestPerformanceMonitor:
    @pytest.fixture
    def performance_monitor():
        from src.scripts.performance_monitor import PerformanceMonitor
        yield PerformanceMonitor()

    def test_happy_path(self, performance_monitor):
        # Mock the subprocess.run to simulate successful connections
        with patch('src.scripts.performance_monitor.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            status = performance_monitor.get_service_status()
            assert status == {
                "redis": True,
                "gateway": True,
                "neural_engine": True,
                "ollama": True
            }

    def test_edge_case_empty_services(self, performance_monitor):
        # Mock an empty services dictionary
        with patch.object(performance_monitor, 'services', {}):
            status = performance_monitor.get_service_status()
            assert status == {}

    def test_edge_case_none_services(self, performance_monitor):
        # Mock services as None
        with patch.object(performance_monitor, 'services', None):
            status = performance_monitor.get_service_status()
            assert status is None

    def test_error_case_invalid_port(self, performance_monitor):
        # Mock a service with an invalid port
        with patch.object(performance_monitor, 'services', {"invalid": 65536}):
            status = performance_monitor.get_service_status()
            assert status == {
                "invalid": False,
                "redis": True,
                "gateway": True,
                "neural_engine": True,
                "ollama": True
            }

    def test_error_case_subprocess_failure(self, performance_monitor):
        # Mock subprocess.run to simulate a failure
        with patch('src.scripts.performance_monitor.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            status = performance_monitor.get_service_status()
            assert status == {
                "redis": False,
                "gateway": False,
                "neural_engine": False,
                "ollama": False
            }