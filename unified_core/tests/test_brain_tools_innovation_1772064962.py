import pytest
from unified_core.brain_tools import db_inject_observation
from unittest.mock import patch, MagicMock

def test_db_inject_observation_happy_path():
    with patch('unified_core.brain_tools.db_query') as mock_db_query:
        result = db_inject_observation(key="test_key", data={"value": 42})
        assert mock_db_query.called_once_with(
            "INSERT OR REPLACE INTO observations (key, value, timestamp) VALUES (?,?,?)",
            ("test_key", '{"value": 42}', pytest.approx(time.time()))
        )
        assert result is None  # Assuming db_query returns None

def test_db_inject_observation_empty_key():
    with patch('unified_core.brain_tools.db_query') as mock_db_query:
        result = db_inject_observation(key="", data={"value": 42})
        assert mock_db_query.called_once_with(
            "INSERT OR REPLACE INTO observations (key, value, timestamp) VALUES (?,?,?)",
            ("", '{"value": 42}', pytest.approx(time.time()))
        )
        assert result is None

def test_db_inject_observation_none_key():
    with patch('unified_core.brain_tools.db_query') as mock_db_query:
        result = db_inject_observation(key=None, data={"value": 42})
        assert mock_db_query.called_once_with(
            "INSERT OR REPLACE INTO observations (key, value, timestamp) VALUES (?,?,?)",
            (None, '{"value": 42}', pytest.approx(time.time()))
        )
        assert result is None

def test_db_inject_observation_empty_data():
    with patch('unified_core.brain_tools.db_query') as mock_db_query:
        result = db_inject_observation(key="test_key", data={})
        assert mock_db_query.called_once_with(
            "INSERT OR REPLACE INTO observations (key, value, timestamp) VALUES (?,?,?)",
            ("test_key", '{}', pytest.approx(time.time()))
        )
        assert result is None

def test_db_inject_observation_none_data():
    with patch('unified_core.brain_tools.db_query') as mock_db_query:
        result = db_inject_observation(key="test_key", data=None)
        assert not mock_db_query.called
        assert result is None

def test_db_inject_observation_invalid_input_type():
    with patch('unified_core.brain_tools.db_query') as mock_db_query:
        result = db_inject_observation(key="test_key", data=12345)
        assert mock_db_query.called_once_with(
            "INSERT OR REPLACE INTO observations (key, value, timestamp) VALUES (?,?,?)",
            ("test_key", '12345', pytest.approx(time.time()))
        )
        assert result is None