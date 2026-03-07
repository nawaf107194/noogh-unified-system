import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
import sqlite3

from unified_core.orchestration.agent_worker import AgentWorker, _DB_PATH

class MockAgentWorker(AgentWorker):
    def __init__(self, db_path: str = None):
        super().__init__(db_path=db_path)

def test_save_understanding_happy_path(mocker):
    # Arrange
    agent_name = "test_agent"
    task_title = "test_task"
    understanding = "This is a test understanding."
    expected_key = f"agent_understanding:{agent_name}:{int(datetime.now().timestamp())}"
    
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mocker.patch.object(sqlite3, 'connect', return_value=mock_conn)
    mock_conn.cursor.return_value = mock_cursor
    
    worker = MockAgentWorker()

    # Act
    result = worker._save_understanding(agent_name, task_title, understanding)

    # Assert
    assert result is None
    mock_conn.connect.assert_called_once_with(_DB_PATH, timeout=5)
    mock_cursor.execute.assert_called_once()
    expected_insert_query = (
        "INSERT OR REPLACE INTO beliefs (key,value,utility_score,updated_at) VALUES (?,?,?,?)"
    )
    expected_value = {
        "agent": agent_name,
        "task": task_title,
        "understanding": understanding,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
    expected_insert_args = (
        (expected_key, json.dumps(expected_value, ensure_ascii=False), 0.85, time.time())
    )
    mock_cursor.execute.assert_called_once_with(expected_insert_query, expected_insert_args)
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()

def test_save_understanding_edge_cases(mocker):
    # Arrange
    agent_name = ""
    task_title = None
    understanding = "This is a test understanding."
    
    worker = MockAgentWorker()

    # Act & Assert
    with pytest.raises(sqlite3.IntegrityError):
        worker._save_understanding(agent_name, task_title, understanding)

def test_save_understanding_empty_inputs(mocker):
    # Arrange
    agent_name = ""
    task_title = ""
    understanding = ""
    
    worker = MockAgentWorker()

    # Act & Assert
    with pytest.raises(sqlite3.IntegrityError):
        worker._save_understanding(agent_name, task_title, understanding)

def test_save_understanding_invalid_utility(mocker):
    # Arrange
    agent_name = "test_agent"
    task_title = "test_task"
    understanding = "This is a test understanding."
    utility = -0.1
    
    worker = MockAgentWorker()

    # Act & Assert
    with pytest.raises(sqlite3.IntegrityError):
        worker._save_understanding(agent_name, task_title, understanding, utility)