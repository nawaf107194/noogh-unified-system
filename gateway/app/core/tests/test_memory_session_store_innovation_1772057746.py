import pytest

from gateway.app.core.memory_session_store import MemorySessionStore

@pytest.fixture
def memory_session_store():
    return MemorySessionStore()

def test_increment_memory_count_happy_path(memory_session_store):
    session_id = "test_session"
    initial_count = 0
    
    # Set initial count to ensure we can increment it
    memory_session_store.sessions[session_id] = {"memory_count": initial_count}
    
    memory_session_store.increment_memory_count(session_id)
    assert memory_session_store.sessions[session_id]["memory_count"] == initial_count + 1

def test_increment_memory_count_edge_case_empty_session_id(memory_session_store):
    session_id = ""
    with pytest.raises(KeyError):
        memory_session_store.increment_memory_count(session_id)

def test_increment_memory_count_edge_case_none_session_id(memory_session_store):
    session_id = None
    with pytest.raises(TypeError):
        memory_session_store.increment_memory_count(session_id)

def test_increment_memory_count_error_case_non_string_session_id(memory_session_store):
    session_id = 12345
    with pytest.raises(TypeError):
        memory_session_store.increment_memory_count(session_id)