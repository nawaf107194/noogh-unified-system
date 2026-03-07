import pytest

class MockMemorySessionStore:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}  # session_id -> session_data

def test_init_happy_path():
    store = MockMemorySessionStore()
    assert isinstance(store.sessions, dict)
    assert not store.sessions

def test_init_edge_case_none_input():
    store = None
    with pytest.raises(TypeError):
        store.__init__()

def test_init_edge_case_empty_string_input():
    store = ""
    with pytest.raises(TypeError):
        store.__init__()