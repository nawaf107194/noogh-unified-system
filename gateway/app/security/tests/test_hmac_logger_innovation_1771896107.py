import pytest
from unittest.mock import patch, mock_open

from gateway.app.security.hmac_logger import HMACLogger

def test_load_last_hash_happy_path():
    """Test normal inputs."""
    log_content = '{"hmac_signature": "hash123"}\n'
    with patch('builtins.open', mock_open(read_data=log_content)) as m:
        hmac_logger = HMACLogger('/path/to/logfile')
        hmac_logger._load_last_hash()
        assert hmac_logger.last_hash == "hash123"

def test_load_last_hash_empty_log():
    """Test empty log file."""
    with patch('builtins.open', mock_open(read_data="")) as m:
        hmac_logger = HMACLogger('/path/to/logfile')
        hmac_logger._load_last_hash()
        assert hmac_logger.last_hash is None

def test_load_last_hash_missing_log_file():
    """Test missing log file."""
    with patch('builtins.open', side_effect=FileNotFoundError):
        hmac_logger = HMACLogger('/path/to/logfile')
        hmac_logger._load_last_hash()
        assert hmac_logger.last_hash is None

def test_load_last_hash_invalid_json():
    """Test log file with invalid JSON."""
    log_content = 'invalid json'
    with patch('builtins.open', mock_open(read_data=log_content)) as m:
        hmac_logger = HMACLogger('/path/to/logfile')
        hmac_logger._load_last_hash()
        assert hmac_logger.last_hash is None