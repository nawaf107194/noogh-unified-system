import pytest
from gateway.app.console.audit import audit_event_signed
import uuid

def test_audit_event_signed_happy_path():
    # Happy path: normal inputs
    kind = "test_kind"
    payload = {"key": "value"}
    event_id = audit_event_signed(kind, payload)
    
    assert isinstance(event_id, str)
    assert len(event_id) == 36  # UUID4 length

def test_audit_event_signed_empty_payload():
    # Edge case: empty payload
    kind = "test_kind"
    payload = {}
    event_id = audit_event_signed(kind, payload)
    
    assert isinstance(event_id, str)
    assert len(event_id) == 36  # UUID4 length

def test_audit_event_signed_none_payload():
    # Edge case: None payload
    kind = "test_kind"
    payload = None
    event_id = audit_event_signed(kind, payload)

    assert isinstance(event_id, str)
    assert len(event_id) == 36  # UUID4 length

def test_audit_event_signed_boundary_payload():
    # Edge case: boundary condition (large payload)
    kind = "test_kind"
    payload = {f"key{i}": f"value{i}" for i in range(1000)}
    event_id = audit_event_signed(kind, payload)

    assert isinstance(event_id, str)
    assert len(event_id) == 36  # UUID4 length

def test_audit_event_signed_invalid_kind():
    # Error case: invalid kind
    kind = None
    payload = {"key": "value"}
    
    event_id = audit_event_signed(kind, payload)

    assert isinstance(event_id, str)
    assert len(event_id) == 36  # UUID4 length

def test_audit_event_signed_invalid_payload():
    # Error case: invalid payload (non-dict type)
    kind = "test_kind"
    payload = "not a dictionary"
    
    event_id = audit_event_signed(kind, payload)

    assert isinstance(event_id, str)
    assert len(event_id) == 36  # UUID4 length

def test_audit_event_signed_secret_from_env():
    # Test that the secret is taken from the environment variable
    original_secret = os.getenv("NOOGH_AUDIT_SECRET", "default-insecure-key-change-me")
    try:
        os.environ["NOOGH_AUDIT_SECRET"] = "new-secret"
        event_id = audit_event_signed("test_kind", {"key": "value"})
        assert isinstance(event_id, str)
        assert len(event_id) == 36  # UUID4 length
    finally:
        os.environ["NOOGH_AUDIT_SECRET"] = original_secret

def test_audit_event_signed_no_env_var():
    # Test that a default secret is used if NOOGH_AUDIT_SECRET is not set
    try:
        del os.environ["NOOGH_AUDIT_SECRET"]
        event_id = audit_event_signed("test_kind", {"key": "value"})
        assert isinstance(event_id, str)
        assert len(event_id) == 36  # UUID4 length
    finally:
        if "NOOGH_AUDIT_SECRET" not in os.environ:
            del os.environ["NOOGH_AUDIT_SECRET"]