import pytest
from unittest.mock import patch, MagicMock

class MockMemorySessionStore:
    def __init__(self):
        self.sessions = {}

    def validate_session(self, session_id: str, token: str) -> bool:
        return session_id in self.sessions and self.sessions[session_id] == token

    def create_session(self, token: str, user_scope: str) -> str:
        session_id = f"session_{len(self.sessions)}"
        self.sessions[session_id] = token
        return session_id

@pytest.fixture
def memory_session_store():
    return MockMemorySessionStore()

def test_get_or_create_session_happy_path(memory_session_store):
    session_id = memory_session_store.get_or_create_session("token123", user_scope="default")
    assert session_id == "session_0"

def test_get_or_create_session_existing_valid_session(memory_session_store):
    memory_session_store.sessions["session_0"] = "token123"
    session_id = memory_session_store.get_or_create_session("token123", user_scope="default", session_id="session_0")
    assert session_id == "session_0"

def test_get_or_create_session_existing_invalid_token(memory_session_store):
    memory_session_store.sessions["session_0"] = "token456"
    session_id = memory_session_store.get_or_create_session("token123", user_scope="default", session_id="session_0")
    assert session_id == "session_1"

def test_get_or_create_session_none_user_scope(memory_session_store):
    with patch.object(memory_session_store, 'create_session') as mock_create:
        session_id = memory_session_store.get_or_create_session("token123", user_scope=None)
        mock_create.assert_called_once_with("token123", "default")
        assert session_id.startswith("session_")

def test_get_or_create_session_empty_token(memory_session_store):
    with patch.object(memory_session_store, 'create_session') as mock_create:
        session_id = memory_session_store.get_or_create_session("")
        mock_create.assert_called_once_with("", "default")
        assert session_id.startswith("session_")

def test_get_or_create_session_none_session_id(memory_session_store):
    with patch.object(memory_session_store, 'create_session') as mock_create:
        session_id = memory_session_store.get_or_create_session("token123", user_scope="default", session_id=None)
        mock_create.assert_called_once_with("token123", "default")
        assert session_id.startswith("session_")

def test_get_or_create_session_boundary_conditions(memory_session_store):
    with patch.object(memory_session_store, 'create_session') as mock_create:
        session_id = memory_session_store.get_or_create_session("token123" * 1000)
        mock_create.assert_called_once_with("token123" * 1000, "default")
        assert len(session_id) == 64

def test_get_or_create_session_invalid_user_scope(memory_session_store):
    with patch.object(memory_session_store, 'create_session') as mock_create:
        session_id = memory_session_store.get_or_create_session("token123", user_scope="invalid")
        mock_create.assert_called_once_with("token123", "default")
        assert session_id.startswith("session_")