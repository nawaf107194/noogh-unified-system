import pytest
from unittest.mock import patch

class StatusMock:
    def __init__(self, status, pid=None, uptime_seconds=0, cpu_percent=0, memory_mb=0, memory_percent=0, num_threads=0, last_cycle_id=None, last_activity=None, arabic_status=""):
        self.status = status
        self.pid = pid
        self.uptime_seconds = uptime_seconds
        self.cpu_percent = cpu_percent
        self.memory_mb = memory_mb
        self.memory_percent = memory_percent
        self.num_threads = num_threads
        self.last_cycle_id = last_cycle_id
        self.last_activity = last_activity
        self.arabic_status = arabic_status

@pytest.fixture
def status_running():
    return StatusMock(
        status="running",
        pid=12345,
        uptime_seconds=3600,
        cpu_percent=15.5,
        memory_mb=1024,
        memory_percent=25.5,
        num_threads=10,
        last_cycle_id="cycle-123",
        last_activity="activity-123",
        arabic_status="稼働中"
    )

@pytest.fixture
def status_stopped():
    return StatusMock(
        status="stopped",
        pid=None,
        uptime_seconds=0,
        cpu_percent=0,
        memory_mb=0,
        memory_percent=0,
        num_threads=0,
        last_cycle_id=None,
        last_activity=None,
        arabic_status="停止中"
    )

def test_print_status_section_running(capfd, status_running):
    print_status_section(status_running)
    out, _ = capfd.readouterr()
    assert "📊 AGENT STATUS | حالة الوكيل" in out
    assert "🟢 Status: running | 稼働中" in out
    assert "PID: 12345" in out
    assert "Uptime: 3600s (60.0 minutes)" in out
    assert "CPU Usage: 15.5%" in out
    assert "Memory: 1024.0 MB (25.5%)" in out
    assert "Threads: 10" in out
    assert "Last Cycle: cycle-123" in out
    assert "Last Activity: activity-123" in out

def test_print_status_section_stopped(capfd, status_stopped):
    print_status_section(status_stopped)
    out, _ = capfd.readouterr()
    assert "📊 AGENT STATUS | حالة الوكيل" in out
    assert "🔴 Status: stopped | 停止中" in out

def test_print_status_section_none(capfd):
    with patch('builtins.print', side_effect=print) as mock_print:
        print_status_section(None)
    assert mock_print.call_count == 2  # Only prints the header and status line

def test_print_status_section_invalid_status(capfd):
    invalid_status = StatusMock(status="invalid", arabic_status="غير صالح")
    with patch('builtins.print', side_effect=print) as mock_print:
        print_status_section(invalid_status)
    assert mock_print.call_count == 2  # Only prints the header and status line