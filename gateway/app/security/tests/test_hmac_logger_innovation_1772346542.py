import pytest
from gateway.app.security.hmac_logger import HMACLogger, AuditEvent

class TestHMACLogger:

    @pytest.fixture
    def hmac_logger(self):
        return HMACLogger()

    @pytest.fixture
    def mock_event(self):
        return AuditEvent(
            event_id="123",
            timestamp=1633072800,
            event_type="login",
            payload="user=john_doe",
            previous_hash="abc123"
        )

    def test_happy_path(self, hmac_logger, mock_event):
        # Happy path: Normal inputs
        result = hmac_logger.verify_event(mock_event)
        assert result is True

    def test_empty_event_id(self, hmac_logger):
        # Edge case: Empty event_id
        event = AuditEvent(
            event_id="",
            timestamp=1633072800,
            event_type="login",
            payload="user=john_doe",
            previous_hash="abc123"
        )
        result = hmac_logger.verify_event(event)
        assert result is False

    def test_none_values(self, hmac_logger):
        # Edge case: None values
        event = AuditEvent(
            event_id=None,
            timestamp=None,
            event_type=None,
            payload=None,
            previous_hash=None
        )
        result = hmac_logger.verify_event(event)
        assert result is False

    def test_invalid_timestamp(self, hmac_logger):
        # Edge case: Invalid timestamp (negative value)
        event = AuditEvent(
            event_id="123",
            timestamp=-1,
            event_type="login",
            payload="user=john_doe",
            previous_hash="abc123"
        )
        result = hmac_logger.verify_event(event)
        assert result is False

    def test_mismatched_signature(self, hmac_logger):
        # Error case: Mismatched HMAC signature
        event = AuditEvent(
            event_id="123",
            timestamp=1633072800,
            event_type="login",
            payload="user=john_doe",
            previous_hash="abc123",
            hmac_signature="invalid_signature"
        )
        result = hmac_logger.verify_event(event)
        assert result is False

    def test_non_string_types(self, hmac_logger):
        # Error case: Non-string types
        event = AuditEvent(
            event_id=123,
            timestamp=1633072800,
            event_type=1.23,
            payload={"user": "john_doe"},
            previous_hash=True
        )
        result = hmac_logger.verify_event(event)
        assert result is False

    def test_async_behavior(self, hmac_logger):
        # Async behavior: Not applicable for this sync function
        pass