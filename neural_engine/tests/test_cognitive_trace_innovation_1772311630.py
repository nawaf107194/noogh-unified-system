import pytest

class CognitiveTrace:
    def __init__(self):
        self.backend_used = None
        self.events = []

    def add_event(self, event_type, data):
        self.events.append((event_type, data))

    def set_backend(self, backend: str):
        """Record which backend is being used."""
        self.backend_used = backend
        self.add_event(TraceEventType.REQUEST_START, {"backend": backend})

class TraceEventType:
    REQUEST_START = "request_start"

def test_set_backend_happy_path():
    cognitive_trace = CognitiveTrace()
    cognitive_trace.set_backend("tensorflow")
    assert cognitive_trace.backend_used == "tensorflow"
    assert cognitive_trace.events == [(TraceEventType.REQUEST_START, {"backend": "tensorflow"})]

def test_set_backend_edge_case_empty_string():
    cognitive_trace = CognitiveTrace()
    cognitive_trace.set_backend("")
    assert cognitive_trace.backend_used == ""
    assert cognitive_trace.events == [(TraceEventType.REQUEST_START, {"backend": ""})]

def test_set_backend_edge_case_none():
    cognitive_trace = CognitiveTrace()
    cognitive_trace.set_backend(None)
    assert cognitive_trace.backend_used is None
    assert cognitive_trace.events == []

def test_set_backend_error_case_invalid_input():
    with pytest.raises(TypeError) as exc_info:
        cognitive_trace = CognitiveTrace()
        cognitive_trace.set_backend(12345)
    assert str(exc_info.value) == "set_backend() argument 'backend' must be a string"