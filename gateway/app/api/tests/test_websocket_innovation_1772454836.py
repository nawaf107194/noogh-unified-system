import pytest

from gateway.app.api.websocket import WebSocket, Gateway

@pytest.fixture
def gateway():
    return Gateway()

@pytest.fixture
def valid_websocket():
    return WebSocket()

def test_disconnect_happy_path(gateway, valid_websocket):
    # Add the WebSocket to active connections
    gateway.active_connections.add(valid_websocket)
    
    # Call the disconnect method
    result = gateway.disconnect(valid_websocket)
    
    # Assert that the WebSocket is removed from active connections
    assert valid_websocket not in gateway.active_connections
    
    # Assert that no error was raised
    assert result is None

def test_disconnect_edge_case_empty(gateway):
    # Call the disconnect method with no active connection
    result = gateway.disconnect(None)
    
    # Assert that no error was raised
    assert result is None

def test_disconnect_error_case_invalid_input(gateway, valid_websocket):
    # Add an invalid input to simulate unexpected behavior
    gateway.active_connections.add("invalid_input")
    
    # Call the disconnect method with an invalid input
    result = gateway.disconnect("invalid_input")
    
    # Assert that the WebSocket is still in active connections (not removed)
    assert "invalid_input" in gateway.active_connections
    
    # Assert that no error was raised
    assert result is None

def test_disconnect_async_behavior(gateway, valid_websocket, event_loop):
    # Add the WebSocket to active connections
    gateway.active_connections.add(valid_websocket)
    
    # Create an asynchronous task to disconnect the WebSocket
    async def disconnect_task():
        await gateway.disconnect(valid_websocket)
    
    # Run the task in the event loop
    result = event_loop.run_until_complete(disconnect_task())
    
    # Assert that the WebSocket is removed from active connections
    assert valid_websocket not in gateway.active_connections
    
    # Assert that no error was raised
    assert result is None