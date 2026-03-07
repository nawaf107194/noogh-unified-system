import pytest
from unittest.mock import patch, mock_open
from gateway.app.api.evolution_api import _read_ledger, LEDGER_FILE
import json

@pytest.fixture
def setup_logging():
    with patch('gateway.app.api.evolution_api.logger.error') as mock_logger:
        yield mock_logger

@pytest.fixture
def mock_file_exists(monkeypatch):
    class MockPath:
        def exists(self):
            return True
    monkeypatch.setattr('pathlib.Path', MockPath)

@pytest.fixture
def mock_file_not_exists(monkeypatch):
    class MockPath:
        def exists(self):
            return False
    monkeypatch.setattr('pathlib.Path', MockPath)

def test_happy_path(mock_file_exists):
    sample_data = [
        '{"id": 1, "event": "login"}',
        '{"id": 2, "event": "logout"}'
    ]
    with patch('builtins.open', mock_open(read_data='\n'.join(sample_data))):
        result = _read_ledger(2)
        assert len(result) == 2
        assert all(isinstance(entry, dict) for entry in result)

def test_empty_file(mock_file_exists):
    sample_data = ['']
    with patch('builtins.open', mock_open(read_data='\n'.join(sample_data))):
        result = _read_ledger(1)
        assert len(result) == 0

def test_none_limit(mock_file_exists):
    sample_data = [
        '{"id": 1, "event": "login"}',
        '{"id": 2, "event": "logout"}'
    ]
    with patch('builtins.open', mock_open(read_data='\n'.join(sample_data))):
        result = _read_ledger(None)
        assert len(result) == 2
        assert all(isinstance(entry, dict) for entry in result)

def test_boundary_limit(mock_file_exists):
    sample_data = [f'{{"id": {i}, "event": "event"}}' for i in range(500)]
    with patch('builtins.open', mock_open(read_data='\n'.join(sample_data))):
        result = _read_ledger(500)
        assert len(result) == 500
        assert all(isinstance(entry, dict) for entry in result)

def test_file_not_exists(mock_file_not_exists):
    result = _read_ledger()
    assert len(result) == 0

def test_invalid_json_entry(mock_file_exists, setup_logging):
    sample_data = [
        '{"id": 1, "event": "login"}',
        '{invalid json}',
        '{"id": 3, "event": "logout"}'
    ]
    with patch('builtins.open', mock_open(read_data='\n'.join(sample_data))):
        result = _read_ledger(3)
        assert len(result) == 2
        assert setup_logging.call_count == 1

def test_read_error(mock_file_exists, setup_logging):
    with patch('builtins.open', side_effect=IOError("File not accessible")):
        result = _read_ledger()
        assert len(result) == 0
        assert setup_logging.call_count == 1

def test_non_integer_limit(mock_file_exists):
    sample_data = [
        '{"id": 1, "event": "login"}',
        '{"id": 2, "event": "logout"}'
    ]
    with patch('builtins.open', mock_open(read_data='\n'.join(sample_data))):
        with pytest.raises(TypeError):
            _read_ledger('not_an_int')