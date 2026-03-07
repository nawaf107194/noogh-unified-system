import pytest

from unified_core.messaging import Messaging

def test_on_happy_path():
    """Test registering a handler for a specific action."""
    messaging = Messaging()
    action = "test_action"
    handler = lambda: "handler_response"

    messaging.on(action, handler)
    
    assert action in messaging._handlers
    assert len(messaging._handlers[action]) == 1
    assert messaging._handlers[action][0] == handler

def test_on_empty_action():
    """Test registering a handler with an empty action."""
    messaging = Messaging()
    action = ""
    handler = lambda: "handler_response"

    messaging.on(action, handler)
    
    assert action in messaging._handlers
    assert len(messaging._handlers[action]) == 1
    assert messaging._handlers[action][0] == handler

def test_on_none_action():
    """Test registering a handler with None as the action."""
    messaging = Messaging()
    action = None
    handler = lambda: "handler_response"

    messaging.on(action, handler)
    
    assert action in messaging._handlers
    assert len(messaging._handlers[action]) == 1
    assert messaging._handlers[action][0] == handler

def test_on_edge_boundary_action():
    """Test registering a handler with the boundary of string length."""
    messaging = Messaging()
    action = "a" * 256  # Assuming default max length is 255 characters
    handler = lambda: "handler_response"

    messaging.on(action, handler)
    
    assert action in messaging._handlers
    assert len(messaging._handlers[action]) == 1
    assert messaging._handlers[action][0] == handler

def test_on_invalid_handler_type():
    """Test registering a handler with an invalid type."""
    messaging = Messaging()
    action = "test_action"
    handler = "not_a_callable"

    messaging.on(action, handler)
    
    assert action in messaging._handlers
    assert len(messaging._handlers[action]) == 1
    assert messaging._handlers[action][0] == handler

def test_on_duplicate_handler():
    """Test registering the same handler multiple times."""
    messaging = Messaging()
    action = "test_action"
    handler = lambda: "handler_response"

    messaging.on(action, handler)
    messaging.on(action, handler)
    
    assert action in messaging._handlers
    assert len(messaging._handlers[action]) == 2
    assert all(h == handler for h in messaging._handlers[action])