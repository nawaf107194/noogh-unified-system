import pytest
from unittest.mock import patch, MagicMock
import time

def mock_request():
    class MockRequest:
        client = None
        is_disconnected = False

    return MockRequest()

@patch('exec_bridge.LOG_PATH.parent.mkdir')
@patch('exec_bridge.LOG_PATH.touch')
@patch('builtins.open', new_callable=MagicMock)
def test_event_stream_happy_path(mock_open, mock_touch, mock_mkdir):
    request = mock_request()
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file

    def readline_side_effect():
        yield "line1\n"
        yield "line2\n"

    mock_file.readline.side_effect = readline_side_effect
    mock_file.readline.return_value = None

    result = list(event_stream(request))

    expected_output = [
        'event: logline\ndata: line1\n\n',
        'event: logline\ndata: line2\n\n',
        ': ping - 0.0\n\n'
    ]

    assert result == expected_output
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_touch.assert_called_once_with(exist_ok=True)
    mock_file.seek.assert_called_once_with(0, os.SEEK_END)

@patch('exec_bridge.LOG_PATH.parent.mkdir')
@patch('exec_bridge.LOG_PATH.touch')
def test_event_stream_client_disconnected(mock_touch, mock_mkdir):
    request = MagicMock(client=None)
    result = list(event_stream(request))

    assert not result
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_touch.assert_called_once_with(exist_ok=True)

@patch('exec_bridge.LOG_PATH.parent.mkdir')
@patch('exec_bridge.LOG_PATH.touch')
def test_event_stream_request_disconnected(mock_touch, mock_mkdir):
    request = MagicMock(is_disconnected=True)
    result = list(event_stream(request))

    assert not result
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_touch.assert_called_once_with(exist_ok=True)

@patch('exec_bridge.LOG_PATH.parent.mkdir')
@patch('exec_bridge.LOG_PATH.touch')
def test_event_stream_file_read_error(mock_touch, mock_mkdir):
    request = mock_request()
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file

    def readline_side_effect():
        yield "line1\n"
        raise IOError("Failed to read file")

    mock_file.readline.side_effect = readline_side_effect
    mock_file.readline.return_value = None

    result = list(event_stream(request))

    expected_output = [
        ': ping - 0.0\n\n'
    ]

    assert result == expected_output
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_touch.assert_called_once_with(exist_ok=True)