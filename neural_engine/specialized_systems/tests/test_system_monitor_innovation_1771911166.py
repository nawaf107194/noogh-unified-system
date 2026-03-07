import pytest
import psutil

class MockProcess:
    def __init__(self, pid):
        self.pid = pid
        self.name = lambda: f"process_{pid}"
        self.status = lambda: "running"
        self.cpu_percent = lambda: 5.0
        self.memory_percent = lambda: 20.0
        self.num_threads = lambda: 1

    def __eq__(self, other):
        return other.pid == self.pid

@pytest.fixture
def mock_process():
    return MockProcess(1234)

class TestSystemMonitor:
    @pytest.mark.parametrize("pid, expected", [
        (1234, {"pid": 1234, "name": "process_1234", "status": "running", "cpu_percent": 5.0, "memory_percent": 20.0, "num_threads": 1}),
        (5678, {"pid": 5678, "name": "process_5678", "status": "running", "cpu_percent": 5.0, "memory_percent": 20.0, "num_threads": 1})
    ])
    def test_get_process_info_happy_path(self, mock_process, pid, expected):
        psutil.Process = lambda p: mock_process if p == pid else None
        system_monitor = SystemMonitor()  # Assume SystemMonitor class is defined elsewhere
        result = system_monitor.get_process_info(pid)
        assert result == expected

    @pytest.mark.parametrize("pid", [None, "", -1])
    def test_get_process_info_edge_cases(self, pid):
        psutil.Process = lambda p: mock_process if p == 1234 else None
        system_monitor = SystemMonitor()
        result = system_monitor.get_process_info(pid)
        assert result == {"error": "Process not found"}

    @pytest.mark.parametrize("pid", ["invalid"])
    def test_get_process_info_error_cases(self, pid):
        psutil.Process = lambda p: mock_process if p == 1234 else None
        system_monitor = SystemMonitor()
        result = system_monitor.get_process_info(pid)
        assert result == {"error": "Process not found"}