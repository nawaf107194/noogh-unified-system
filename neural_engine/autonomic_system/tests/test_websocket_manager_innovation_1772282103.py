import pytest
from unittest.mock import Mock, patch
from neural_engine.autonomic_system.websocket_manager import WebSocketManager

def test_disconnect_happy_path():
    # Arrange
    websocket_manager = WebSocketManager()
    websocket_manager.active_connections = [Mock(), Mock()]
    
    # Act
    result = websocket_manager.disconnect(websocket_manager.active_connections[0])
    
    # Assert
    assert len(websocket_manager.active_connections) == 1
    assert result is None

def test_disconnect_empty_connections():
    # Arrange
    websocket_manager = WebSocketManager()
    websocket_manager.active_connections = []
    
    # Act
    result = websocket_manager.disconnect(Mock())
    
    # Assert
    assert len(websocket_manager.active_connections) == 0
    assert result is None

def test_disconnect_none_websocket():
    # Arrange
    websocket_manager = WebSocketManager()
    websocket_manager.active_connections = [Mock()]
    
    # Act
    result = websocket_manager.disconnect(None)
    
    # Assert
    assert len(websocket_manager.active_connections) == 1
    assert result is None

def test_disconnect_invalid_websocket_type():
    # Arrange
    websocket_manager = WebSocketManager()
    websocket_manager.active_connections = [Mock()]
    
    with patch('neural_engine.autonomic_system.websocket_manager.logger.info') as mock_info:
        result = websocket_manager.disconnect("not a websocket")
        
        # Assert
        assert len(websocket_manager.active_connections) == 1
        assert result is None
        mock_info.assert_not_called()