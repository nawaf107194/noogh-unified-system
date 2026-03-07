import pytest
from typing import.Dict, Any

class CognitiveTrace:
    def __init__(self):
        self.traces = []

    def get_recent_traces(self, n: int) -> List[str]:
        return self.traces[-n:]

    def add_trace(self, trace):
        self.traces.append(trace)

def test_get_dashboard_data_happy_path():
    ct = CognitiveTrace()
    trace1 = {"total_duration_ms": 200, "iterations": 5, "total_tool_calls": 3, "successful_tool_calls": 2}
    trace2 = {"total_duration_ms": 300, "iterations": 7, "total_tool_calls": 4, "successful_tool_calls": 3}
    ct.add_trace(trace1)
    ct.add_trace(trace2)

    result = ct.get_dashboard_data()

    assert result == {
        "total_requests": 2,
        "avg_duration_ms": 250.0,
        "avg_iterations": 6.0,
        "tool_success_rate": 75.0,
        "backends_used": [],
        "recent_traces": [trace2, trace1]
    }

def test_get_dashboard_data_empty():
    ct = CognitiveTrace()

    result = ct.get_dashboard_data()

    assert result == {
        "total_requests": 0,
        "avg_duration_ms": 0,
        "avg_iterations": 0,
        "tool_success_rate": 0,
        "backends_used": [],
        "recent_traces": []
    }

def test_get_dashboard_data_single_trace():
    ct = CognitiveTrace()
    trace1 = {"total_duration_ms": 200, "iterations": 5, "total_tool_calls": 3, "successful_tool_calls": 2}
    ct.add_trace(trace1)

    result = ct.get_dashboard_data()

    assert result == {
        "total_requests": 1,
        "avg_duration_ms": 200.0,
        "avg_iterations": 5.0,
        "tool_success_rate": 66.7,
        "backends_used": [],
        "recent_traces": [trace1]
    }

def test_get_dashboard_data_tool_success_rate_zero():
    ct = CognitiveTrace()
    trace1 = {"total_duration_ms": 200, "iterations": 5, "total_tool_calls": 3, "successful_tool_calls": 0}
    ct.add_trace(trace1)

    result = ct.get_dashboard_data()

    assert result == {
        "total_requests": 1,
        "avg_duration_ms": 200.0,
        "avg_iterations": 5.0,
        "tool_success_rate": 0.0,
        "backends_used": [],
        "recent_traces": [trace1]
    }

def test_get_dashboard_data_with_backends():
    ct = CognitiveTrace()
    trace1 = {"total_duration_ms": 200, "iterations": 5, "total_tool_calls": 3, "successful_tool_calls": 2, "backend_used": "A"}
    trace2 = {"total_duration_ms": 300, "iterations": 7, "total_tool_calls": 4, "successful_tool_calls": 3, "backend_used": "B"}
    ct.add_trace(trace1)
    ct.add_trace(trace2)

    result = ct.get_dashboard_data()

    assert result == {
        "total_requests": 2,
        "avg_duration_ms": 250.0,
        "avg_iterations": 6.0,
        "tool_success_rate": 75.0,
        "backends_used": ["A", "B"],
        "recent_traces": [trace2, trace1]
    }