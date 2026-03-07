import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json

from shared.event_logger import EventLogger

@pytest.fixture
def event_logger(tmpdir):
    log_file = str(tmpdir.join('test_log.json'))
    return EventLogger(log_file)

@patch('builtins.open', new_callable=MagicMock)
def test_log_event_happy_path(mock_open, event_logger):
    event_type = 'state_change'
    details = {'user_id': 123, 'new_state': 'active'}
    
    event_logger.log_event(event_type, details)
    
    mock_open.assert_called_once_with(event_logger.log_file, 'a')
    file_handle = mock_open.return_value.__enter__.return_value
    assert file_handle.write.call_count == 1
    log_entry = json.loads(file_handle.write.call_args[0][0])
    assert log_entry['timestamp']
    assert log_entry['type'] == event_type
    assert log_entry['details'] == details

def test_log_event_empty_details(event_logger):
    event_type = 'state_change'
    details = {}
    
    result = event_logger.log_event(event_type, details)
    
    assert result is None
    
@patch('builtins.open', side_effect=IOError("I/O error"))
def test_log_event_io_error(mock_open, event_logger):
    event_type = 'state_change'
    details = {'user_id': 123, 'new_state': 'active'}
    
    result = event_logger.log_event(event_type, details)
    
    assert result is None
    mock_open.assert_called_once_with(event_logger.log_file, 'a')

def test_log_event_none_details(event_logger):
    event_type = 'state_change'
    details = None
    
    result = event_logger.log_event(event_type, details)
    
    assert result is None
    
def test_log_event_invalid_event_type(event_logger):
    event_type = 123
    details = {'user_id': 123, 'new_state': 'active'}
    
    result = event_logger.log_event(event_type, details)
    
    assert result is None
    
def test_log_event_empty_event_type(event_logger):
    event_type = ''
    details = {'user_id': 123, 'new_state': 'active'}
    
    result = event_logger.log_event(event_type, details)
    
    assert result is None