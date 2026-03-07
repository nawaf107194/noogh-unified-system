import pytest
from src.unified_core.orchestration.messages import Message

@pytest.fixture
def valid_message_fields():
    return {
        "trace_id": "test_trace_id",
        "task_id": "test_task_id",
        "sender": "test_sender",
        "receiver": "test_receiver"
    }

@pytest.fixture
def message_class():
    return Message

def test___post_init___happy_path(valid_message_fields, message_class):
    # Test with all required fields populated
    try:
        message_class(**valid_message_fields)
    except ValueError:
        pytest.fail("Happy path failed unexpectedly")

def test___post_init___missing_trace_id(message_class, valid_message_fields):
    valid_message_fields["trace_id"] = ""
    with pytest.raises(ValueError, match="trace_id is REQUIRED"):
        message_class(**valid_message_fields)

def test___post_init___missing_task_id(message_class, valid_message_fields):
    valid_message_fields["task_id"] = None
    with pytest.raises(ValueError, match="task_id is REQUIRED"):
        message_class(**valid_message_fields)

def test___post_init___missing_sender(message_class, valid_message_fields):
    valid_message_fields["sender"] = ""
    with pytest.raises(ValueError, match="sender is REQUIRED"):
        message_class(**valid_message_fields)

def test___post_init___missing_receiver(message_class, valid_message_fields):
    valid_message_fields["receiver"] = None
    with pytest.raises(ValueError, match="receiver is REQUIRED"):
        message_class(**valid_message_fields)