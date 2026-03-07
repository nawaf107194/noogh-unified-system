import pytest
from unittest.mock import patch, MagicMock
from unified_core.core.coercive_memory import CoerciveMemory, Blocker

@pytest.fixture
def coercive_memory():
    return CoerciveMemory()

@patch('os.makedirs')
@patch('open', new_callable=MagicMock)
def test_persist_blocker_happy_path(mock_open, mock_makedirs, coercive_memory):
    blocker = Blocker(id="123", type="test_type", data={"key": "value"})
    coercive_memory.STORAGE_LOCATIONS = ['/tmp/test_loc']
    
    coercive_memory._persist_blocker(blocker)
    
    mock_makedirs.assert_called_once_with('/tmp/test_loc', exist_ok=True)
    mock_open.assert_called_once_with('/tmp/test_loc/blockers.jsonl', 'a')
    mock_open.return_value.write.assert_called_once()

@patch('os.makedirs', side_effect=OSError("Permission denied"))
def test_persist_blocker_error_path(mock_makedirs, coercive_memory):
    blocker = Blocker(id="123", type="test_type", data={"key": "value"})
    coercive_memory.STORAGE_LOCATIONS = ['/tmp/test_loc']
    
    coercive_memory._persist_blocker(blocker)
    
    mock_makedirs.assert_called_once_with('/tmp/test_loc', exist_ok=True)

@patch('os.makedirs')
def test_persist_blocker_edge_case_empty_storage_locations(mock_makedirs, coercive_memory):
    blocker = Blocker(id="123", type="test_type", data={"key": "value"})
    coercive_memory.STORAGE_LOCATIONS = []
    
    coercive_memory._persist_blocker(blocker)
    
    mock_makedirs.assert_not_called()

@patch('os.makedirs')
def test_persist_blocker_edge_case_none_storage_locations(mock_makedirs, coercive_memory):
    blocker = Blocker(id="123", type="test_type", data={"key": "value"})
    coercive_memory.STORAGE_LOCATIONS = None
    
    coercive_memory._persist_blocker(blocker)
    
    mock_makedirs.assert_not_called()