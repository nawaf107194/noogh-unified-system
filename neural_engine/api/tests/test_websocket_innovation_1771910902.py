import pytest

from neural_engine.api.websocket import WebsocketAPI  # Adjust the import as necessary

def test_get_active_count_happy_path():
    websocket = WebsocketAPI()
    websocket.active_connections = set([1, 2, 3])
    assert websocket.get_active_count() == 3

def test_get_active_count_empty():
    websocket = WebsocketAPI()
    websocket.active_connections = set()
    assert websocket.get_active_count() == 0

def test_get_active_count_none():
    websocket = WebsocketAPI()
    websocket.active_connections = None
    assert websocket.get_active_count() == 0

def test_get_active_count_boundary():
    websocket = WebsocketAPI()
    websocket.active_connections = set([1])
    assert websocket.get_active_count() == 1