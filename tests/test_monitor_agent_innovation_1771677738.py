import pytest

from monitor_agent import print_status_section

class MockStatus:
    def __init__(self, status="running", pid=None, uptime_seconds=0, cpu_percent=0, memory_mb=0, memory_percent=0, num_threads=0, last_cycle_id=None, last_activity=None):
        self.status = status
        self.arabic_status = "تشغيل" if status == "running" else "توقف"
        self.pid = pid
        self.uptime_seconds = uptime_seconds
        self.cpu_percent = cpu_percent
        self.memory_mb = memory_mb
        self.memory_percent = memory_percent
        self.num_threads = num_threads
        self.last_cycle_id = last_cycle_id
        self.last_activity = last_activity

def test_print_status_section_happy_path():
    status = MockStatus(status="running", pid=1234, uptime_seconds=3600, cpu_percent=5.5, memory_mb=2048, memory_percent=75, num_threads=10, last_cycle_id="cycle1", last_activity="task1")
    captured_output = capsys.readouterr()
    print_status_section(status)
    assert "📊 AGENT STATUS | حالة الوكيل" in captured_output.out
    assert "PID: 1234" in captured_output.out
    assert "Uptime: 3600s (60.0 minutes)" in captured_output.out
    assert "CPU Usage: 5.5%" in captured_output.out
    assert "Memory: 2048 MB (75.0%)" in captured_output.out
    assert "Threads: 10" in captured_output.out
    assert "Last Cycle: cycle1" in captured_output.out
    assert "Last Activity: task1" in captured_output.out

def test_print_status_section_edge_cases():
    status_empty = MockStatus()
    captured_output = capsys.readouterr()
    print_status_section(status_empty)
    assert "📊 AGENT STATUS | حالة الوكيل" in captured_output.out
    assert "PID: None" in captured_output.out
    assert "Uptime: 0s (0.0 minutes)" in captured_output.out
    assert "CPU Usage: 0.0%" in captured_output.out
    assert "Memory: 0.0 MB (0.0%)" in captured_output.out
    assert "Threads: 0" in captured_output.out
    assert "Last Cycle: None" in captured_output.out
    assert "Last Activity: None" in captured_output.out

def test_print_status_section_error_cases():
    status_invalid = MockStatus(status="invalid")
    captured_output = capsys.readouterr()
    print_status_section(status_invalid)
    assert "📊 AGENT STATUS | حالة الوكيل" in captured_output.out
    assert "PID: None" in captured_output.out
    assert "Uptime: 0s (0.0 minutes)" in captured_output.out
    assert "CPU Usage: 0.0%" in captured_output.out
    assert "Memory: 0.0 MB (0.0%)" in captured_output.out
    assert "Threads: 0" in captured_output.out
    assert "Last Cycle: None" in captured_output.out
    assert "Last Activity: None" in captured_output.out

def test_print_status_section_async_behavior():
    # Since the function is synchronous, no need for async testing here.
    pass