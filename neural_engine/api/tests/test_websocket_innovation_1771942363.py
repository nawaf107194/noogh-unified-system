import pytest

from neural_engine.api.websocket import WebSocket, WebSocketManager

class TestWebSocketManagerDisconnect:

    @pytest.fixture
    def manager(self):
        return WebSocketManager()

    @pytest.fixture
    def websocket(self):
        return WebSocket()

    def test_happy_path(self, manager, websocket):
        """Normal inputs."""
        client_id = "test_client"
        manager.connection_metadata[websocket] = {"client_id": client_id}
        manager.active_connections.add(websocket)
        
        result = manager.disconnect(websocket)
        
        assert result is None
        assert websocket not in manager.active_connections
        assert client_id not in {metadata["client_id"] for metadata in manager.connection_metadata.values()}
        logger.info.assert_called_once_with(f"WebSocket disconnected: {client_id}")

    def test_edge_case_empty(self, manager):
        """Empty input."""
        result = manager.disconnect(None)
        
        assert result is None
        assert len(manager.active_connections) == 0
        assert len(manager.connection_metadata) == 0

    def test_error_case_invalid_input(self, manager):
        """Invalid input type."""
        with pytest.raises(TypeError) as exc_info:
            manager.disconnect(123)

        assert str(exc_info.value) == "Expected a WebSocket object"