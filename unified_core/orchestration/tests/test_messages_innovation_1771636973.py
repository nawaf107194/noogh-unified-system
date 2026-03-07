import pytest
from unified_core.orchestration.messages import Message, RiskLevel, TaskType

@pytest.fixture
def sample_message():
    return Message(
        message_id="12345",
        trace_id="abcde",
        task_id="task123",
        sender="userA",
        receiver="userB",
        type=TaskType.INFO,
        risk_level=RiskLevel.LOW,
        scopes=["scope1", "scope2"],
        payload={"key": "value"},
        timestamp="2023-04-10T12:34:56Z",
        ttl_ms=3600,
        retry_count=0
    )

def test_to_dict_happy_path(sample_message):
    result = sample_message.to_dict()
    assert isinstance(result, dict)
    assert result['message_id'] == "12345"
    assert result['trace_id'] == "abcde"
    assert result['task_id'] == "task123"
    assert result['sender'] == "userA"
    assert result['receiver'] == "userB"
    assert result['type'] == TaskType.INFO.value
    assert result['risk_level'] == RiskLevel.LOW.value
    assert result['scopes'] == ["scope1", "scope2"]
    assert result['payload'] == {"key": "value"}
    assert result['timestamp'] == "2023-04-10T12:34:56Z"
    assert result['ttl_ms'] == 3600
    assert result['retry_count'] == 0

def test_to_dict_empty_values():
    message = Message(
        message_id="",
        trace_id=None,
        task_id=None,
        sender=None,
        receiver=None,
        type=TaskType.INFO,
        risk_level=RiskLevel.LOW,
        scopes=[],
        payload={},
        timestamp=None,
        ttl_ms=None,
        retry_count=None
    )
    result = message.to_dict()
    assert isinstance(result, dict)
    assert result['message_id'] == ""
    assert result['trace_id'] is None
    assert result['task_id'] is None
    assert result['sender'] is None
    assert result['receiver'] is None
    assert result['type'] == TaskType.INFO.value
    assert result['risk_level'] == RiskLevel.LOW.value
    assert result['scopes'] == []
    assert result['payload'] == {}
    assert result['timestamp'] is None
    assert result['ttl_ms'] is None
    assert result['retry_count'] is None

def test_to_dict_invalid_type():
    with pytest.raises(TypeError):
        Message(
            message_id="12345",
            trace_id="abcde",
            task_id="task123",
            sender="userA",
            receiver="userB",
            type="INVALID_TYPE",
            risk_level=RiskLevel.LOW,
            scopes=["scope1", "scope2"],
            payload={"key": "value"},
            timestamp="2023-04-10T12:34:56Z",
            ttl_ms=3600,
            retry_count=0
        )

def test_to_dict_invalid_risk_level():
    with pytest.raises(ValueError):
        Message(
            message_id="12345",
            trace_id="abcde",
            task_id="task123",
            sender="userA",
            receiver="userB",
            type=TaskType.INFO,
            risk_level="INVALID_RISK_LEVEL",
            scopes=["scope1", "scope2"],
            payload={"key": "value"},
            timestamp="2023-04-10T12:34:56Z",
            ttl_ms=3600,
            retry_count=0
        )