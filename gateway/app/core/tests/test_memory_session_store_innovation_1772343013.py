import pytest
from datetime import datetime, timedelta

class MockSessionStore:
    def __init__(self):
        self.sessions = {}

    def validate_session(self, session_id: str, token: str) -> bool:
        """
        Validate that session exists, is not expired, and matches token.

        Args:
            session_id: Session identifier
            token: Bearer token to verify

        Returns:
            True if session is valid, False otherwise
        """
        session = self.sessions.get(session_id)

        if not session:
            logger.warning(f"Memory session {session_id[:16]}... not found")
            return False

        # Check expiration
        if session["expires"] < datetime.utcnow():
            logger.info(f"Memory session {session_id[:16]}... expired")
            del self.sessions[session_id]
            return False

        # Verify token match
        if session["token"] != token:
            logger.warning(f"Token mismatch for memory session {session_id[:16]}...")
            return False

        return True


@pytest.fixture
def session_store():
    return MockSessionStore()


def test_validate_session_happy_path(session_store):
    session_id = "session123"
    token = "valid_token"
    expires_at = datetime.utcnow() + timedelta(hours=1)
    session_store.sessions[session_id] = {
        "token": token,
        "expires": expires_at
    }

    result = session_store.validate_session(session_id, token)
    assert result is True


def test_validate_session_empty_session_id(session_store):
    token = "valid_token"
    result = session_store.validate_session("", token)
    assert result is False


def test_validate_session_none_session_id(session_store):
    token = "valid_token"
    result = session_store.validate_session(None, token)
    assert result is False


def test_validate_session_expired_session(session_store):
    session_id = "session123"
    token = "valid_token"
    expires_at = datetime.utcnow() - timedelta(hours=1)
    session_store.sessions[session_id] = {
        "token": token,
        "expires": expires_at
    }

    result = session_store.validate_session(session_id, token)
    assert result is False


def test_validate_session_mismatched_token(session_store):
    session_id = "session123"
    valid_token = "valid_token"
    invalid_token = "invalid_token"
    expires_at = datetime.utcnow() + timedelta(hours=1)
    session_store.sessions[session_id] = {
        "token": valid_token,
        "expires": expires_at
    }

    result = session_store.validate_session(session_id, invalid_token)
    assert result is False


def test_validate_session_session_not_found(session_store):
    session_id = "session123"
    token = "valid_token"

    result = session_store.validate_session(session_id, token)
    assert result is False