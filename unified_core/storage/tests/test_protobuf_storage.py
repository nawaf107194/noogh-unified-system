import pytest
from unittest.mock import patch, MagicMock
from os.path import exists

from unified_core.storage.protobuf_storage import ProtobufStorage

class MockProtobufStorage(ProtobufStorage):
    def __init__(self):
        super().__init__()
        self.saved_innovations = []

    def save_innovation(self, innovation):
        self.saved_innovations.append(innovation)

    def _dict_to_innovation_pb(self, data):
        if 'id' in data and 'name' in data:
            return data
        else:
            return None

@pytest.fixture
def storage():
    return MockProtobufStorage()

@patch('builtins.open', new_callable=MagicMock)
def test_happy_path(mock_open, storage):
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    mock_file.readlines.return_value = [
        '{"id": "1", "name": "Innovation 1"}\n',
        '{"id": "2", "name": "Innovation 2"}\n'
    ]

    count = storage.convert_from_jsonl('path/to/jsonl')
    
    assert count == 2
    assert len(storage.saved_innovations) == 2

@patch('builtins.open', new_callable=MagicMock)
def test_empty_file(mock_open, storage):
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    mock_file.readlines.return_value = []

    count = storage.convert_from_jsonl('path/to/jsonl')
    
    assert count == 0
    assert len(storage.saved_innovations) == 0

@patch('builtins.open', new_callable=MagicMock)
def test_none_path(mock_open, storage):
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    exists.return_value = False

    count = storage.convert_from_jsonl(None)
    
    assert count == 0
    assert len(storage.saved_innovations) == 0

@patch('builtins.open', new_callable=MagicMock)
def test_invalid_json(mock_open, storage):
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    mock_file.readlines.return_value = [
        '{"id": "1", "name": "Innovation 1"}\n',
        'invalid json\n'
    ]

    count = storage.convert_from_jsonl('path/to/jsonl')
    
    assert count == 1
    assert len(storage.saved_innovations) == 1

@patch('builtins.open', new_callable=MagicMock)
def test_async_behavior(mock_open, storage):
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    mock_file.readlines.return_value = [
        '{"id": "1", "name": "Innovation 1"}\n',
        '{"id": "2", "name": "Innovation 2"}\n'
    ]

    storage.convert_from_jsonl('path/to/jsonl')
    
    assert len(storage.saved_innovations) == 2