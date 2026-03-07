import pytest
from unittest.mock import patch, MagicMock
from forensics_tracer import hooked_popen

# Mock the original popen and log_event functions
original_popen = hooked_popen.__wrapped__

@patch('forensics_tracer.log_event')
def test_happy_path(log_event_mock):
    result = hooked_popen(['ls', '-l'], cwd='/home/user', env={'PATH': '/bin'})
    assert result is not None
    log_event_mock.assert_called_once_with("subprocess_spawn", {
        "command": ['ls', '-l'],
        "cwd": '/home/user',
        "env_keys": ['PATH'],
        "stack": []
    })

def test_edge_case_empty_args():
    result = hooked_popen()
    assert result is None

@patch('forensics_tracer.log_event')
def test_edge_case_none_env(log_event_mock):
    result = hooked_popen(['echo', 'test'], cwd='/home/user', env=None)
    assert result is not None
    log_event_mock.assert_called_once_with("subprocess_spawn", {
        "command": ['echo', 'test'],
        "cwd": '/home/user',
        "env_keys": [],
        "stack": []
    })

@patch('forensics_tracer.log_event')
def test_edge_case_empty_env(log_event_mock):
    result = hooked_popen(['echo', 'test'], cwd='/home/user', env={})
    assert result is not None
    log_event_mock.assert_called_once_with("subprocess_spawn", {
        "command": ['echo', 'test'],
        "cwd": '/home/user',
        "env_keys": [],
        "stack": []
    })

@patch('forensics_tracer.log_event')
def test_async_behavior(log_event_mock):
    result = hooked_popen(['sleep', '1'], cwd='/home/user', env={'PATH': '/bin'}, stdout=MagicMock())
    assert result is not None
    log_event_mock.assert_called_once_with("subprocess_spawn", {
        "command": ['sleep', '1'],
        "cwd": '/home/user',
        "env_keys": ['PATH'],
        "stack": []
    })
    result.stdout.write.assert_called_once_with(b'')