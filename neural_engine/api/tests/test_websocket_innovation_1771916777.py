import pytest

class MockWebSocketAPI:
    def __init__(self):
        self.active_connections = []

    def get_active_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)

@pytest.fixture
def websocket_api():
    return MockWebSocketAPI()

def test_get_active_count_happy_path(websocket_api):
    # Arrange
    websocket_api.active_connections = [1, 2, 3]

    # Act
    result = websocket_api.get_active_count()

    # Assert
    assert result == 3

def test_get_active_count_edge_case_empty(websocket_api):
    # Arrange
    websocket_api.active_connections = []

    # Act
    result = websocket_api.get_active_count()

    # Assert
    assert result == 0

def test_get_active_count_edge_case_none(websocket_api):
    # Arrange
    websocket_api.active_connections = None

    # Act
    result = websocket_api.get_active_count()

    # Assert
    assert result == 0

def test_get_active_count_error_case_invalid_input(websocket_api):
    with pytest.raises(TypeError) as exc_info:
        websocket_api.active_connections.append("invalid")
    
    # Assert
    with pytest.raises(TypeError) as exc_info:
        websocket_api.get_active_count()

    assert "object of type 'str' has no len()" in str(exc_info.value)