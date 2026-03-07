import pytest
from gateway.app.console.audit import audit_event_signed
import uuid
from typing import Dict, Any

@pytest.fixture
def hmac_logger(mocker):
    class MockHMACLogger:
        def log_event(self, event_id: str, event_type: str, payload: Dict[str, Any]) -> str:
            return event_id
    
    mocker.patch('gateway.app.security.hmac_logger.get_hmac_logger', return_value=MockHMACLogger())
    yield None

def test_audit_event_signed_happy_path(hmac_logger):
    kind = "login"
    payload = {"user_id": "123", "timestamp": "2023-04-01T12:00:00Z"}
    result = audit_event_signed(kind, payload)
    assert isinstance(result, str)
    assert uuid.UUID(result, version=4)  # Ensure it's a valid UUID

def test_audit_event_signed_empty_payload(hmac_logger):
    kind = "empty"
    payload = {}
    result = audit_event_signed(kind, payload)
    assert isinstance(result, str)
    assert uuid.UUID(result, version=4)  # Ensure it's a valid UUID

def test_audit_event_signed_none_payload(hmac_logger):
    kind = "none"
    payload = None
    with pytest.raises(TypeError):
        audit_event_signed(kind, payload)

def test_audit_event_signed_invalid_kind_type(hmac_logger):
    kind = 123
    payload = {"user_id": "123", "timestamp": "2023-04-01T12:00:00Z"}
    with pytest.raises(TypeError):
        audit_event_signed(kind, payload)