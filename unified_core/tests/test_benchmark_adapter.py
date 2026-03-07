import pytest

class BenchmarkAdapter:
    def __init__(self, successful_tool_calls=0, failed_tool_calls=0, blocked_tool_calls=0):
        self.successful_tool_calls = successful_tool_calls
        self.failed_tool_calls = failed_tool_calls
        self.blocked_tool_calls = blocked_tool_calls

    def blocked_rate(self) -> float:
        total = self.successful_tool_calls + self.failed_tool_calls + self.blocked_tool_calls
        if total == 0:
            return 0.0
        return self.blocked_tool_calls / total

def test_blocked_rate_happy_path():
    adapter = BenchmarkAdapter(10, 5, 3)
    assert adapter.blocked_rate() == 0.3

def test_blocked_rate_empty_values():
    adapter = BenchmarkAdapter(0, 0, 0)
    assert adapter.blocked_rate() == 0.0

def test_blocked_rate_only_failed_calls():
    adapter = BenchmarkAdapter(0, 10, 5)
    assert adapter.blocked_rate() == 0.3333333333333333

def test_blocked_rate_only_successful_calls():
    adapter = BenchmarkAdapter(10, 0, 0)
    assert adapter.blocked_rate() == 0.0

def test_blocked_rate_only_blocked_calls():
    adapter = BenchmarkAdapter(0, 0, 5)
    assert adapter.blocked_rate() == 1.0