import pytest
from unittest.mock import MagicMock
from neural_engine.autonomic_system.websocket_manager import get_ws_manager, WebSocketManager

# Mock the WebSocketManager class to avoid actual instantiation and network calls
WebSocketManager = MagicMock()

# Global variable to simulate the singleton pattern
_ws_manager = None

@pytest.fixture(autouse=True)
def reset_singleton():
    global _ws_manager
    _ws_manager = None

def test_happy_path():
    # Test the normal case where the singleton is created and returned
    manager = get_ws_manager()
    assert manager == _ws_manager
    WebSocketManager.assert_called_once()

def test_edge_case_no_initialization():
    # Test edge case where the singleton has not been initialized yet
    global _ws_manager
    _ws_manager = None
    manager = get_ws_manager()
    assert manager == _ws_manager
    WebSocketManager.assert_called_once()

def test_async_behavior():
    # Since the function does not involve async operations, this test is more about ensuring the function is synchronous
    import asyncio
    
    async def async_test():
        manager = await asyncio.to_thread(get_ws_manager)
        assert manager == _ws_manager
        WebSocketManager.assert_called_once()
    
    asyncio.run(async_test())

def test_error_case_invalid_input():
    # The function does not take any input, so this test checks if calling with an argument raises a TypeError
    with pytest.raises(TypeError):
        get_ws_manager(None)

def test_multiple_calls_return_same_instance():
    # Ensure that multiple calls to the function return the same instance
    first_call = get_ws_manager()
    second_call = get_ws_manager()
    assert first_call == second_call
    WebSocketManager.assert_called_once()