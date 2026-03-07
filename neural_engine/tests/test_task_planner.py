import pytest
from unittest.mock import patch, mock_open
from datetime import datetime

from neural_engine.task_planner import TaskPlanner

@pytest.fixture
def task_planner():
    return TaskPlanner()

def test_execute_task_happy_path(task_planner):
    task_id = "123"
    task = {"id": task_id, "steps": [{"step": 1}, {"step": 2}]}
    with patch.object(task_planner, '_get_task', return_value=task) as mock_get_task:
        result = task_planner.execute_task(task_id)
        assert result == {'task_id': task_id, 'status': 'completed', 'progress': 1.0}
        mock_get_task.assert_called_once_with(task_id)

def test_execute_task_no_steps(task_planner):
    task_id = "456"
    task = {"id": task_id}
    with patch.object(task_planner, '_get_task', return_value=task) as mock_get_task:
        result = task_planner.execute_task(task_id)
        assert result == {'task_id': task_id, 'status': 'completed', 'progress': 1.0}
        mock_get_task.assert_called_once_with(task_id)

def test_execute_task_invalid_task_id(task_planner):
    task_id = "789"
    with patch.object(task_planner, '_get_task', return_value=None) as mock_get_task:
        result = task_planner.execute_task(task_id)
        assert result == {'error': 'Task not found'}
        mock_get_task.assert_called_once_with(task_id)

def test_execute_task_empty_steps(task_planner):
    task_id = "101"
    task = {"id": task_id, "steps": []}
    with patch.object(task_planner, '_get_task', return_value=task) as mock_get_task:
        result = task_planner.execute_task(task_id)
        assert result == {'task_id': task_id, 'status': 'completed', 'progress': 1.0}
        mock_get_task.assert_called_once_with(task_id)

def test_execute_task_async_behavior_no_steps(task_planner):
    task_id = "102"
    task = {"id": task_id}
    with patch.object(task_planner, '_get_task', return_value=task) as mock_get_task:
        with patch('neural_engine.task_planner.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = '2023-04-01T12:00:00'
            result = task_planner.execute_task(task_id)
            assert result == {'task_id': task_id, 'status': 'completed', 'progress': 1.0}
            mock_get_task.assert_called_once_with(task_id)
            mock_datetime.now.assert_called_once()

def test_execute_task_async_behavior_with_steps(task_planner):
    task_id = "103"
    task = {"id": task_id, "steps": [{"step": 1}, {"step": 2}]}
    with patch.object(task_planner, '_get_task', return_value=task) as mock_get_task:
        with patch('neural_engine.task_planner.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = '2023-04-01T12:00:00'
            result = task_planner.execute_task(task_id)
            assert result == {'task_id': task_id, 'status': 'completed', 'progress': 1.0}
            mock_get_task.assert_called_once_with(task_id)
            mock_datetime.now.assert_has_calls([mock.call(), mock.call()])