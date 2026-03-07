import pytest
from unified_core.messaging import AgentMessage, from_bytes, MessageType, MessagePriority

# Happy path (normal inputs)
def test_from_bytes_happy_path():
    data = b'{"id": "123", "source": "agent1", "target": "agent2", "type": "request", "action": "fetch", "payload": {"key": "value"}, "ts": 1633072800, "priority": "high"}'
    message = from_bytes(data)
    assert isinstance(message, AgentMessage)
    assert message.id == "123"
    assert message.source_agent == "agent1"
    assert message.target_agent == "agent2"
    assert message.message_type == MessageType.request
    assert message.action == "fetch"
    assert message.payload == {"key": "value"}
    assert message.timestamp == 1633072800
    assert message.priority == MessagePriority.high
    assert message.correlation_id is None
    assert message.ttl_seconds == 300
    assert message.metadata == {}

# Edge cases (empty, None, boundaries)
def test_from_bytes_empty_data():
    data = b''
    message = from_bytes(data)
    assert message is None

def test_from_bytes_none_data():
    message = from_bytes(None)
    assert message is None

def test_from_bytes_invalid_json():
    data = b'{"id": "123", "source": "agent1", "target": "agent2", "type": "request", "action": "fetch", "payload": {"key": "value"}, "ts": 1633072800, "priority": "high"'
    message = from_bytes(data)
    assert message is None

# Error cases (invalid inputs) - No specific exceptions raised in the code, so no tests needed for this case

# Async behavior (if applicable) - Not applicable as the function is synchronous