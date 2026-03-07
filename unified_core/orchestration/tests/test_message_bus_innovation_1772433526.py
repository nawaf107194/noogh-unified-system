import pytest

from unified_core.orchestration.message_bus import MessageBus

@pytest.fixture
def message_bus():
    return MessageBus()

def test_subscribe_happy_path(message_bus):
    topic = "agent:code_executor"
    callback = lambda x: None
    
    result = message_bus.subscribe(topic, callback)
    
    assert result is None
    assert len(message_bus._subscribers[topic]) == 1

def test_subscribe_empty_topic(message_bus):
    topic = ""
    callback = lambda x: None
    
    result = message_bus.subscribe(topic, callback)
    
    assert result is None
    assert len(message_bus._subscribers[topic]) == 1

def test_subscribe_none_topic(message_bus):
    topic = None
    callback = lambda x: None
    
    result = message_bus.subscribe(topic, callback)
    
    assert result is None
    assert len(message_bus._subscribers[None]) == 1

def test_subscribe_empty_callback(message_bus):
    topic = "agent:code_executor"
    callback = None
    
    with pytest.raises(TypeError) as exc_info:
        message_bus.subscribe(topic, callback)
    
    assert str(exc_info.value) == "Callback must be a callable"

def test_subscribe_none_callback(message_bus):
    topic = "agent:code_executor"
    callback = None
    
    with pytest.raises(TypeError) as exc_info:
        message_bus.subscribe(topic, callback)
    
    assert str(exc_info.value) == "Callback must be a callable"