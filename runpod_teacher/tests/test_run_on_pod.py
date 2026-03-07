import pytest
from unittest.mock import mock_open, patch
from datetime import datetime
import requests

from runpod_teacher.run_on_pod import main, call_teacher, score_response

# Mocking the imports and functions
@patch('requests.get')
@patch('runpod_teacher.run_on_pod.call_teacher')
@patch('random.shuffle')
@patch('time.sleep')
@patch('runpod_teacher.run_on_pod.TASKS', [("Category1", "Task1"), ("Category2", "Task2")])
def test_main_happy_path(mock_sleep, mock_shuffle, mock_call_teacher, mock_get):
    mock_get.return_value.status_code = 200
    mock_call_teacher.return_value = {
        "success": True, "content": "hello", "input_tokens": 10, "output_tokens": 10, "latency_ms": 100
    }
    
    mock_open_handle = mock_open()
    with patch('builtins.open', mock_open_handle):
        main()

    # Assertions
    assert mock_get.called
    assert mock_shuffle.called
    assert mock_sleep.called
    # Check file writing
    handle = mock_open_handle()
    assert handle.write.called

@patch('requests.get')
def test_main_teacher_api_not_reachable(mock_get):
    # Setup mock data
    mock_output_file = '/tmp/output.jsonl'
    
    mock_get.side_effect = requests.exceptions.RequestException
    
    # main() catches this exception and returns cleanly, not throwing SystemExit
    main()
    
    # Assert get was called to verify path was taken
    assert mock_get.called

@patch('requests.get')
@patch('random.shuffle')
@patch('time.sleep')
@patch('runpod_teacher.run_on_pod.TASKS', [])
def test_main_empty_tasks(mock_sleep, mock_shuffle, mock_get):
    mock_get.return_value.status_code = 200
    
    with patch('builtins.open', mock_open()):
        main()

    # Assertions
    mock_sleep.assert_not_called()
    assert mock_shuffle.called

@patch('requests.get')
@patch('random.shuffle')
@patch('runpod_teacher.run_on_pod.TASKS', [("Category1", "Task1"), ("Category2", "Task2")])
def test_main_call_teacher_failure(mock_shuffle, mock_get):
    mock_get.return_value.status_code = 200
    
    with patch('builtins.open', mock_open()):
        with patch('runpod_teacher.run_on_pod.call_teacher') as mock_call_teacher:
            mock_call_teacher.return_value = {"success": False, "error": "Failed to call teacher"}
            
            # Since main loops and doesn't exit, we just run it and assert it hit the loop
            main()
    
    # Assertions
    assert mock_call_teacher.called

@patch('requests.get')
@patch('random.shuffle')
@patch('runpod_teacher.run_on_pod.TASKS', [("Category1", "Task1")])
@patch('runpod_teacher.run_on_pod.call_teacher')
def test_main_score_response_failure(mock_call_teacher, mock_shuffle, mock_get):
    mock_get.return_value.status_code = 200
    mock_call_teacher.return_value = {"success": True, "content": "x", "input_tokens": 1, "output_tokens": 1, "latency_ms": 1}
    
    with patch('builtins.open', mock_open()):
        with patch('runpod_teacher.run_on_pod.score_response') as mock_score_response:
            mock_score_response.return_value = 0.5
            
            main()

    # Assertions
    assert mock_score_response.called

@patch('requests.get')
@patch('random.shuffle')
@patch('runpod_teacher.run_on_pod.TASKS', [("Category1", "Task1")])
def test_main_large_output_tokens(mock_shuffle, mock_get):
    mock_get.return_value.status_code = 200
    
    with patch('builtins.open', mock_open()):
        with patch('runpod_teacher.run_on_pod.call_teacher') as mock_call_teacher:
            mock_call_teacher.return_value = {
                "success": True,
                "content": "a" * 100000,
                "input_tokens": 200,
                "output_tokens": 100000,
                "latency_ms": 500
            }
            
            main()

    # Assertions
    assert mock_call_teacher.called