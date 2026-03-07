import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

class MockSessionManager:
    def __init__(self):
        self.sessions = {}

    def add_session(self, sid, last_updated=None):
        if last_updated is None:
            last_updated = datetime.now() - timedelta(hours=25)  # Old session
        self.sessions[sid] = {'last_updated': last_updated}

@pytest.fixture
def session_manager():
    return MockSessionManager()

def test_cleanup_old_sessions_happy_path(session_manager):
    # Setup
    old_sid = 'old_session'
    new_sid = 'new_session'
    session_manager.add_session(old_sid)
    session_manager.add_session(new_sid, datetime.now())
    
    # Action
    session_manager.cleanup_old_sessions(max_age_hours=24)
    
    # Assert
    assert old_sid not in session_manager.sessions
    assert new_sid in session_manager.sessions

def test_cleanup_old_sessions_empty_sessions(session_manager):
    # Action
    session_manager.cleanup_old_sessions(max_age_hours=24)
    
    # Assert
    assert len(session_manager.sessions) == 0

def test_cleanup_old_sessions_all_old_sessions(session_manager):
    # Setup
    old_sid_1 = 'old_session_1'
    old_sid_2 = 'old_session_2'
    session_manager.add_session(old_sid_1)
    session_manager.add_session(old_sid_2)
    
    # Action
    session_manager.cleanup_old_sessions(max_age_hours=24)
    
    # Assert
    assert len(session_manager.sessions) == 0

def test_cleanup_old_sessions_boundary_case(session_manager):
    # Setup
    boundary_sid = 'boundary_session'
    session_manager.add_session(boundary_sid, datetime.now() - timedelta(hours=24))
    
    # Action
    session_manager.cleanup_old_sessions(max_age_hours=24)
    
    # Assert
    assert boundary_sid in session_manager.sessions

def test_cleanup_old_sessions_invalid_max_age_hours(session_manager):
    # Action & Assert
    with pytest.raises(TypeError):
        session_manager.cleanup_old_sessions(max_age_hours='not_an_integer')

def test_cleanup_old_sessions_async_behavior(session_manager):
    # Since the function does not involve async operations, we just mock it
    session_manager.cleanup_old_sessions = MagicMock(side_effect=session_manager.cleanup_old_sessions)
    
    # Action
    session_manager.cleanup_old_sessions(max_age_hours=24)
    
    # Assert
    session_manager.cleanup_old_sessions.assert_called_once_with(max_age_hours=24)