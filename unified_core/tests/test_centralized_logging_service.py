import pytest
from unittest.mock import mock_open, patch
from centralized_logging_service import CentralizedLoggingService
import os

@pytest.fixture
def logging_service():
    service = CentralizedLoggingService()
    service.logs = {"log1": "message1", "log2": "message2"}
    return service

@pytest.mark.parametrize("filename", ["test_logs.json", "another_log_file.txt"])
def test_dump_logs_happy_path(logging_service, filename):
    with patch('builtins.open', mock_open()) as mock_file:
        logging_service.dump_logs(filename)
        mock_file.assert_called_once_with(filename, 'w')
        handle = mock_file()
        handle.write.assert_called_once()

def test_dump_logs_default_filename(logging_service):
    default_filename = 'logs.json'
    with patch('builtins.open', mock_open()) as mock_file:
        logging_service.dump_logs()
        mock_file.assert_called_once_with(default_filename, 'w')

def test_dump_logs_empty_logs(logging_service):
    logging_service.logs = {}
    with patch('builtins.open', mock_open()) as mock_file:
        logging_service.dump_logs()
        mock_file.assert_called_once_with('logs.json', 'w')
        handle = mock_file()
        handle.write.assert_called_once()

def test_dump_logs_none_filename(logging_service):
    with pytest.raises(TypeError):
        logging_service.dump_logs(None)

def test_dump_logs_invalid_filename(logging_service):
    invalid_filename = 12345
    with pytest.raises(TypeError):
        logging_service.dump_logs(invalid_filename)

def test_dump_logs_file_exists(logging_service):
    with patch('os.path.exists', return_value=True) as mock_exists:
        with patch('builtins.open', mock_open()) as mock_file:
            logging_service.dump_logs()
            mock_exists.assert_called_once_with('logs.json')
            mock_file.assert_called_once_with('logs.json', 'w')

def test_dump_logs_file_not_writeable(logging_service):
    with patch('os.access', side_effect=lambda path, mode: False if mode == os.W_OK else True):
        with pytest.raises(PermissionError):
            logging_service.dump_logs('/root/restricted/logs.json')

# Note: For async behavior, the given function does not support async operations.
# If the function were to be made async in the future, tests would need to be updated accordingly.