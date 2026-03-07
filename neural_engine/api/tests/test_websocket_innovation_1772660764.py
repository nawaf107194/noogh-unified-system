import pytest
from neural_engine.api.websocket import WebSocketManager

@pytest.fixture
def websocket_manager():
    return WebSocketManager()

def test_get_active_count_happy_path(websocket_manager):
    # Add some test connections
    test_connections = ["conn1", "conn2", "conn3"]
    websocket_manager.active_connections.extend(test_connections)
    
    # Test normal case with active connections
    assert websocket_manager.get_active_count() == 3
    
    # Test count after removing some connections
    websocket_manager.active_connections.remove("conn1")
    assert websocket_manager.get_active_count() == 2

def test_get_active_count_empty(websocket_manager):
    # Test empty connections
    assert websocket_manager.get_active_count() == 0

def test_get_active_count_all_removed(websocket_manager):
    # Add and then remove all connections
    test_connections = ["conn1", "conn2"]
    websocket_manager.active_connections.extend(test_connections)
    for conn in test_connections:
        websocket_manager.active_connections.remove(conn)
        
    assert websocket_manager.get_active_count() == 0