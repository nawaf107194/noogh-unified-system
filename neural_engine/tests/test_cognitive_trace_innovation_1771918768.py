import pytest
from typing import List, Dict, Any

class MockTrace:
    def __init__(self, trace_id: int):
        self.trace_id = trace_id

    def to_dict(self) -> Dict[str, Any]:
        return {'trace_id': self.trace_id}

class CognitiveTraceManager:
    def __init__(self):
        self.traces = []

    def add_trace(self, trace: MockTrace):
        self.traces.append(trace)

    def get_recent_traces(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent traces for dashboard display."""
        recent = self.traces[-limit:]
        return [t.to_dict() for t in reversed(recent)]

def test_get_recent_traces_happy_path():
    manager = CognitiveTraceManager()
    for i in range(15):
        manager.add_trace(MockTrace(i))
    
    # Test with default limit
    result = manager.get_recent_traces()
    assert len(result) == 10
    assert result[0]['trace_id'] == 14
    assert result[-1]['trace_id'] == 5
    
    # Test with custom limit
    result = manager.get_recent_traces(limit=5)
    assert len(result) == 5
    assert result[0]['trace_id'] == 14
    assert result[-1]['trace_id'] == 10

def test_get_recent_traces_empty():
    manager = CognitiveTraceManager()
    result = manager.get_recent_traces()
    assert result == []

def test_get_recent_traces_none():
    manager = CognitiveTraceManager()
    manager.traces = None
    result = manager.get_recent_traces()
    assert result is None

def test_get_recent_traces_boundary_limit():
    manager = CognitiveTraceManager()
    for i in range(3):
        manager.add_trace(MockTrace(i))
    
    # Test with limit greater than available traces
    result = manager.get_recent_traces(limit=5)
    assert len(result) == 3
    assert result[0]['trace_id'] == 2

def test_get_recent_traces_negative_limit():
    manager = CognitiveTraceManager()
    for i in range(10):
        manager.add_trace(MockTrace(i))
    
    # Test with negative limit (should return all traces)
    result = manager.get_recent_traces(limit=-5)
    assert len(result) == 10
    assert result[0]['trace_id'] == 9

def test_get_recent_traces_limit_zero():
    manager = CognitiveTraceManager()
    for i in range(10):
        manager.add_trace(MockTrace(i))
    
    # Test with limit zero (should return empty list)
    result = manager.get_recent_traces(limit=0)
    assert result == []