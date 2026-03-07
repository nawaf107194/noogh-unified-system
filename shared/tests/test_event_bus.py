import pytest

from src.shared.event_bus import EventBus

@pytest.fixture
def event_bus():
    return EventBus()

def test_publish_event_happy_path(event_bus):
    event_type = "user_logged_in"
    data = {"user_id": 123}
    
    result = event_bus.publish_event(event_type, data)
    
    assert result is None
    assert not event_bus._event_queue.empty()
    event = event_bus._event_queue.get()
    assert event == (event_type, data)

def test_publish_event_empty_data(event_bus):
    event_type = "user_logged_in"
    data = {}
    
    result = event_bus.publish_event(event_type, data)
    
    assert result is None
    assert not event_bus._event_queue.empty()
    event = event_bus._event_queue.get()
    assert event == (event_type, data)

def test_publish_event_none_data(event_bus):
    event_type = "user_logged_in"
    data = None
    
    result = event_bus.publish_event(event_type, data)
    
    assert result is None
    assert not event_bus._event_queue.empty()
    event = event_bus._event_queue.get()
    assert event == (event_type, data)

def test_publish_event_boundary_data(event_bus):
    event_type = "user_logged_in"
    data = {"large_number": 10**9}
    
    result = event_bus.publish_event(event_type, data)
    
    assert result is None
    assert not event_bus._event_queue.empty()
    event = event_bus._event_queue.get()
    assert event == (event_type, data)

def test_publish_event_invalid_types(event_bus):
    event_type = "user_logged_in"
    data = {"invalid": [1, 2, 3]}
    
    result = event_bus.publish_event(event_type, data)
    
    assert result is None
    assert not event_bus._event_queue.empty()
    event = event_bus._event_queue.get()
    assert event == (event_type, data)