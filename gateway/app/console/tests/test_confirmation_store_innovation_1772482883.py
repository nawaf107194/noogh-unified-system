import pytest
from datetime import datetime, timedelta
from gateway.app.console.confirmation_store import ConfirmationStore

class TestConfirmationStore:

    @pytest.fixture
    def confirmation_store(self):
        return ConfirmationStore()

    def test_cleanup_expired_happy_path(self, confirmation_store):
        # Arrange
        now = datetime.utcnow()
        expires_later = now + timedelta(days=1)
        expires_now = now
        expires_earlier = now - timedelta(days=1)

        confirmation_store.pending = {
            'nonce1': {'expires': expires_later},
            'nonce2': {'expires': expires_now},
            'nonce3': {'expires': expires_earlier}
        }

        # Act
        confirmation_store.cleanup_expired()

        # Assert
        assert 'nonce1' in confirmation_store.pending
        assert 'nonce2' not in confirmation_store.pending
        assert 'nonce3' not in confirmation_store.pending

    def test_cleanup_expired_empty(self, confirmation_store):
        # Arrange
        confirmation_store.pending = {}

        # Act
        confirmation_store.cleanup_expired()

        # Assert
        assert not confirmation_store.pending

    def test_cleanup_expired_none(self, confirmation_store):
        confirmation_store.pending = None

        with pytest.raises(AttributeError):
            confirmation_store.cleanup_expired()

    def test_cleanup_expired_boundary(self, confirmation_store):
        now = datetime.utcnow()
        expires_at_now = now

        confirmation_store.pending = {
            'nonce1': {'expires': expires_at_now}
        }

        # Act
        confirmation_store.cleanup_expired()

        # Assert
        assert 'nonce1' not in confirmation_store.pending