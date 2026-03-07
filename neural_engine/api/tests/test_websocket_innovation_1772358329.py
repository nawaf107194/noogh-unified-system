import pytest

class MockWebSocket:
    pass

def test_init_happy_path():
    ws = WebSocket()
    assert isinstance(ws.active_connections, list)
    assert len(ws.active_connections) == 0
    assert isinstance(ws.connection_metadata, dict)
    assert len(ws.connection_metadata) == 0

def test_init_empty_input():
    ws = WebSocket(None)
    assert isinstance(ws.active_connections, list)
    assert len(ws.active_connections) == 0
    assert isinstance(ws.connection_metadata, dict)
    assert len(ws.connection_metadata) == 0

def test_init_boundary_case_large_input():
    large_list = [MockWebSocket() for _ in range(1000)]
    ws = WebSocket(large_list)
    assert isinstance(ws.active_connections, list)
    assert len(ws.active_connections) == 1000
    assert isinstance(ws.connection_metadata, dict)
    assert len(ws.connection_metadata) == 1000

def test_init_error_case_invalid_input():
    with pytest.raises(TypeError):
        WebSocket("Invalid input")