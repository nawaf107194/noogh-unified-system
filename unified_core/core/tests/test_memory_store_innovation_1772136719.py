import pytest
from unittest.mock import patch, MagicMock
from contextlib import closing

class MockConnection:
    def execute(self, query, params):
        pass

def mock_get_connection():
    return MockConnection()

@pytest.fixture(autouse=True)
@patch('noogh_unified_system.src.unified_core.core.memory_store._get_connection', side_effect=mock_get_connection)
def setup(mock_get_conn):
    from noogh_unified_system.src.unified_core.core.memory_store import MemoryStore
    yield MemoryStore()
    mock_get_conn.reset_mock()

def test_record_experience_sync_happy_path(memory_store):
    result = memory_store._record_experience_sync(
        experience_id="123",
        context="test_context",
        action="test_action",
        outcome="test_outcome",
        success=True
    )
    assert result is None

def test_record_experience_sync_empty_string(memory_store):
    with pytest.raises(ValueError) as excinfo:
        memory_store._record_experience_sync(
            experience_id="",
            context="test_context",
            action="test_action",
            outcome="test_outcome",
            success=True
        )
    assert "experience_id cannot be empty" in str(excinfo.value)

def test_record_experience_sync_none_values(memory_store):
    with pytest.raises(ValueError) as excinfo:
        memory_store._record_experience_sync(
            experience_id=None,
            context="test_context",
            action="test_action",
            outcome="test_outcome",
            success=True
        )
    assert "experience_id cannot be None" in str(excinfo.value)

def test_record_experience_sync_invalid_success_type(memory_store):
    with pytest.raises(ValueError) as excinfo:
        memory_store._record_experience_sync(
            experience_id="123",
            context="test_context",
            action="test_action",
            outcome="test_outcome",
            success="not_a_bool"
        )
    assert "success must be a boolean" in str(excinfo.value)

def test_record_experience_sync_boundary_values(memory_store):
    result = memory_store._record_experience_sync(
        experience_id="12345678901234567890",
        context="a" * 1000,
        action="b" * 1000,
        outcome="c" * 1000,
        success=False
    )
    assert result is None

def test_record_experience_sync_async_behavior(memory_store):
    # Since the function is synchronous, this test is not applicable.
    pass