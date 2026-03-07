import pytest

from gateway.app.analytics.event_store import EventStore, get_event_store

# Mock the global _store variable to simulate its behavior
_store = None

def test_get_event_store_happy_path():
    # Call the function multiple times to ensure it returns the same instance
    store1 = get_event_store()
    store2 = get_event_store()
    
    assert store1 is store2  # Ensure it's a singleton
    assert isinstance(store1, EventStore)
    assert store1.max_events == 5000

def test_get_event_store_edge_cases():
    global _store
    
    # Simulate the _store being already set to None
    _store = None
    store1 = get_event_store()
    assert store1 is not None
    assert isinstance(store1, EventStore)
    
    # Simulate the _store being already set to a non-None value
    class MockEventStore:
        def __init__(self):
            pass
    
    _store = MockEventStore()
    store2 = get_event_store()
    assert store2 is not None
    assert isinstance(store2, EventStore)

def test_get_event_store_error_cases():
    # There are no error cases in the provided function as it does not raise exceptions
    pass

# Note: Async behavior is not applicable since the function is synchronous and does not involve asynchronous operations.