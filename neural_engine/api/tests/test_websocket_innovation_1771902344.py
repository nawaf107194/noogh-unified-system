import pytest

from neural_engine.api.websocket import WebSocketManager  # Adjust the import as needed

def test_get_active_count_happy_path():
    """Test the normal operation with active connections."""
    ws_manager = WebSocketManager()
    ws_manager.active_connections = ['conn1', 'conn2']
    assert ws_manager.get_active_count() == 2

def test_get_active_count_empty_connections():
    """Test the case when there are no active connections."""
    ws_manager = WebSocketManager()
    ws_manager.active_connections = []
    assert ws_manager.get_active_count() == 0

def test_get_active_count_none_connections():
    """Test the case when active connections is None."""
    ws_manager = WebSocketManager()
    ws_manager.active_connections = None
    assert ws_manager.get_active_count() == 0

def test_get_active_count_boundary_case():
    """Test the boundary case with a single connection."""
    ws_manager = WebSocketManager()
    ws_manager.active_connections = ['conn1']
    assert ws_manager.get_active_count() == 1

# Note: There are no error cases or async behavior to test in this function