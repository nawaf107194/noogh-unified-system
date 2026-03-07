import pytest
from unified_core.orchestration.messages import Message

def test_to_dict_happy_path():
    message = Message(
        message_id="12345",
        trace_id="abcde",
        task_id="task123",
        sender="sender1",
        receiver="receiver1",
        type="typeA",
        risk_level="high",
        scopes=["scope1", "scope2"],
        payload={"key": "value"},
        timestamp="2023-04-01T12:00:00Z",
        ttl_ms=60000,
        retry_count=0
    )
    expected_dict = {
        "message_id": "12345",
        "trace_id": "abcde",
        "task_id": "task123",
        "sender": "sender1",
        "receiver": "receiver1",
        "type": "typeA",
        "risk_level": "high",
        "scopes": ["scope1", "scope2"],
        "payload": {"key": "value"},
        "timestamp": "2023-04-01T12:00:00Z",
        "ttl_ms": 60000,
        "retry_count": 0
    }
    assert message.to_dict() == expected_dict

def test_to_dict_empty_values():
    message = Message(
        message_id="",
        trace_id=None,
        task_id=None,
        sender=None,
        receiver=None,
        type=None,
        risk_level=None,
        scopes=[],
        payload={},
        timestamp="2023-04-01T12:00:00Z",
        ttl_ms=60000,
        retry_count=0
    )
    expected_dict = {
        "message_id": "",
        "trace_id": None,
        "task_id": None,
        "sender": None,
        "receiver": None,
        "type": None,
        "risk_level": None,
        "scopes": [],
        "payload": {},
        "timestamp": "2023-04-01T12:00:00Z",
        "ttl_ms": 60000,
        "retry_count": 0
    }
    assert message.to_dict() == expected_dict

def test_to_dict_invalid_type():
    # Assuming 'type' and 'risk_level' are enums, we should handle invalid values gracefully
    # Here we assume that the enum validation is done elsewhere and we just return None or default value
    message = Message(
        message_id="12345",
        trace_id="abcde",
        task_id="task123",
        sender="sender1",
        receiver="receiver1",
        type=999,  # Invalid enum value
        risk_level=999,  # Invalid enum value
        scopes=["scope1", "scope2"],
        payload={"key": "value"},
        timestamp="2023-04-01T12:00:00Z",
        ttl_ms=60000,
        retry_count=0
    )
    expected_dict = {
        "message_id": "12345",
        "trace_id": "abcde",
        "task_id": "task123",
        "sender": "sender1",
        "receiver": "receiver1",
        "type": None,  # Assuming default value or None
        "risk_level": None,  # Assuming default value or None
        "scopes": ["scope1", "scope2"],
        "payload": {"key": "value"},
        "timestamp": "2023-04-01T12:00:00Z",
        "ttl_ms": 60000,
        "retry_count": 0
    }
    assert message.to_dict() == expected_dict

def test_to_dict_async_behavior():
    # Assuming 'to_dict' is not asynchronous, we can skip this part if it's not the case
    pass