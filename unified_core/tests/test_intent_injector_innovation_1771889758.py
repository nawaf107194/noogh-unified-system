import pytest
from unittest.mock import patch
from datetime import datetime, timezone
from unified_core.intent_injector import IntentInjector

@pytest.fixture
def intent_injector():
    return IntentInjector(db_path="test_db.sqlite")

@patch('unified_core.intent_injector.sqlite3.connect')
def test_mark_completed_happy_path(mock_connect, intent_injector):
    mock_cursor = mock_connect.return_value.cursor.return_value
    intent_id = 123

    intent_injector.mark_completed(intent_id)

    mock_connect.assert_called_once_with("test_db.sqlite")
    mock_cursor.execute.assert_called_once_with(
        "UPDATE intents SET status = 'completed', processed_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), intent_id)
    )
    mock_connect.return_value.commit.assert_called_once()
    mock_connect.return_value.close.assert_called_once()

@patch('unified_core.intent_injector.sqlite3.connect')
def test_mark_completed_edge_case_none(mock_connect, intent_injector):
    intent_id = None

    with pytest.raises(TypeError) as exc_info:
        intent_injector.mark_completed(intent_id)

    assert str(exc_info.value) == "intent_id cannot be None"

@patch('unified_core.intent_injector.sqlite3.connect')
def test_mark_completed_edge_case_empty(mock_connect, intent_injector):
    intent_id = ""

    with pytest.raises(ValueError) as exc_info:
        intent_injector.mark_completed(intent_id)

    assert str(exc_info.value) == "intent_id cannot be an empty string"

@patch('unified_core.intent_injector.sqlite3.connect')
def test_mark_completed_edge_case_zero(mock_connect, intent_injector):
    intent_id = 0

    with pytest.raises(ValueError) as exc_info:
        intent_injector.mark_completed(intent_id)

    assert str(exc_info.value) == "intent_id cannot be zero"

@patch('unified_core.intent_injector.sqlite3.connect')
def test_mark_completed_error_case_negative(mock_connect, intent_injector):
    intent_id = -1

    with pytest.raises(ValueError) as exc_info:
        intent_injector.mark_completed(intent_id)

    assert str(exc_info.value) == "intent_id cannot be negative"