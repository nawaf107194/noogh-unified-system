import pytest
from .event_store import EventStore  # Adjust the import path as necessary

@pytest.fixture
def event_store():
    return EventStore(seen_max=100)

@pytest.mark.parametrize("event, expected", [
    ({"name": "click", "data": {"id": "evt_123"}}, True),
    ({"name": "view"}, True),  # Missing 'id' should be handled
])
def test_happy_path(event_store, event, expected):
    assert event_store.add_event(event) == expected

@pytest.mark.parametrize("event", [
    None,
    {},
    {"unknown_key": "value"},
])
def test_edge_cases(event_store, event):
    assert not event_store.add_event(event)

def test_error_cases(event_store):
    # The function does not explicitly raise exceptions
    pass

async def test_async_behavior():
    # This function is not async, so no need for this test
    pass