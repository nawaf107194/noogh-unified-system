import pytest

class MockSessionManager:
    def __init__(self):
        self.sessions = {}

    def delete_session(self, session_id: str):
        """Delete session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

def test_delete_session_happy_path():
    manager = MockSessionManager()
    manager.sessions['123'] = 'some_data'
    manager.delete_session('123')
    assert '123' not in manager.sessions

def test_delete_session_empty_input():
    manager = MockSessionManager()
    result = manager.delete_session('')
    assert result is None
    assert len(manager.sessions) == 0

def test_delete_session_none_input():
    manager = MockSessionManager()
    result = manager.delete_session(None)
    assert result is None
    assert len(manager.sessions) == 0

def test_delete_session_non_existent_id():
    manager = MockSessionManager()
    result = manager.delete_session('123')
    assert result is None
    assert len(manager.sessions) == 0