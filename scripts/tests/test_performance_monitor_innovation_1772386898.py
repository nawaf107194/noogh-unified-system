import pytest
from pathlib import Path
from unittest.mock import patch

class TestPerformanceMonitorInit:

    @pytest.fixture
    def performance_monitor():
        return PerformanceMonitor()

    def test_happy_path(self, performance_monitor):
        assert isinstance(performance_monitor.data_dir, Path)
        assert performance_monitor.data_dir == Path(__file__).parent.parent / "data" / "performance"
        assert performance_monitor.data_dir.exists()

    @patch("pathlib.Path.mkdir")
    def test_edge_case_no_parents(self, mock_mkdir, performance_monitor):
        with patch.object(performance_monitor.data_dir.parent, "exists", return_value=False) as mock_exists:
            mock_exists.return_value = False
            mock_mkdir.assert_not_called()
            performance_monitor.__init__()
            assert not performance_monitor.data_dir.exists()

    @patch("pathlib.Path.mkdir")
    def test_error_case_invalid_path(self, mock_mkdir):
        with patch.object(Path, "mkdir", side_effect=FileNotFoundError) as mock_mkdir:
            pm = PerformanceMonitor()
            assert isinstance(pm.data_dir, Path)
            assert not pm.data_dir.exists()