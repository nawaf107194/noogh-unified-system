import pytest
from datetime import datetime
from typing import List
from unittest.mock import patch, MagicMock
from gateway.app.core.persistent_memory import PersistentMemory

class TestPersistentMemory:

    @pytest.fixture
    def persistent_memory(self):
        with patch('gateway.app.core.persistent_memory.atomic_write_json', autospec=True) as mock_write:
            yield PersistentMemory(mock_write)

    @pytest.mark.parametrize("session_id, turns, expected_length", [
        ("12345", [ConversationTurn(user="user1", message="hello"), ConversationTurn(user="bot", message="hi")], 1),
        ("67890", [], 0),
        (None, [ConversationTurn(user="user1", message="hello")], 0),
    ])
    def test_save_conversation_happy_path(self, persistent_memory, session_id, turns, expected_length):
        persistent_memory.save_conversation(session_id, turns)
        persistent_memory.atomic_write_json.assert_called_once()
        data = persistent_memory.atomic_write_json.call_args[0][1]
        assert len(data) == expected_length

    def test_save_conversation_existing_session(self, persistent_memory):
        persistent_memory._load_conversations.return_value = [
            {
                "session_id": "12345",
                "timestamp": datetime.now().isoformat(),
                "turns": [asdict(ConversationTurn(user="user1", message="hello"))]
            }
        ]
        persistent_memory.save_conversation("12345", [ConversationTurn(user="bot", message="hi")])
        persistent_memory.atomic_write_json.assert_called_once()
        data = persistent_memory.atomic_write_json.call_args[0][1]
        assert len(data) == 1
        assert data[0]["turns"][-1]["message"] == "hi"

    def test_save_conversation_boundary_cases(self, persistent_memory):
        persistent_memory._load_conversations.return_value = [
            {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "turns": [asdict(ConversationTurn(user="user1", message="hello"))]
            } for session_id in range(50)
        ]
        persistent_memory.save_conversation("new_session", [ConversationTurn(user="bot", message="hi")])
        persistent_memory.atomic_write_json.assert_called_once()
        data = persistent_memory.atomic_write_json.call_args[0][1]
        assert len(data) == 50
        assert data[-1]["session_id"] == "new_session"

    @pytest.mark.parametrize("session_id, turns", [
        (None, [ConversationTurn(user="user1", message="hello")]),
        ("12345", None),
        ("12345", [ConversationTurn(message="missing_user")]),
    ])
    def test_save_conversation_invalid_inputs(self, persistent_memory, session_id, turns):
        result = persistent_memory.save_conversation(session_id, turns)
        assert result is None
        persistent_memory.atomic_write_json.assert_not_called()