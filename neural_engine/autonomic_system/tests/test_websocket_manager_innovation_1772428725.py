import pytest

from neural_engine.autonomic_system.websocket_manager import WebSocketManager, logger

class MockWebSocket:
    def __init__(self):
        self.id = "test_websocket"

@pytest.fixture
def websocket_manager():
    return WebSocketManager()

def test_disconnect_happy_path(websocket_manager):
    mock_websocket = MockWebSocket()
    websocket_manager.active_connections.add(mock_websocket)
    
    result = websocket_manager.disconnect(mock_websocket)
    
    assert len(websocket_manager.active_connections) == 0
    logger.info.assert_called_once_with("🔌 Client disconnected (remaining: 0)")

def test_disconnect_empty_connection_list(websocket_manager):
    mock_websocket = MockWebSocket()
    
    result = websocket_manager.disconnect(mock_websocket)
    
    assert len(websocket_manager.active_connections) == 0
    logger.info.assert_not_called()

def test_disconnect_none_input(websocket_manager, caplog):
    with caplog.at_level(logging.INFO):
        result = websocket_manager.disconnect(None)
    
    assert len(websocket_manager.active_connections) == 0
    assert "Unexpected None input" in caplog.text

def test_disconnect_invalid_input(websocket_manager, caplog):
    with caplog.at_level(logging.ERROR):
        result = websocket_manager.disconnect("not a WebSocket")
    
    assert len(websocket_manager.active_connections) == 0
    assert "Invalid input type" in caplog.text