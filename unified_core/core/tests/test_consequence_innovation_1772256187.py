import pytest
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

class MockConsequenceSystem:
    STORAGE_LOCATIONS = ['/mock/location1', '/mock/location2']
    
    def __init__(self, storage_name):
        self._storage_name = storage_name
    
    @staticmethod
    def _read_from_file(filepath):
        return [{'hash': 'hash1', 'data': 'data1'}, {'hash': 'hash2', 'data': 'data2'}]
    
    @staticmethod
    def _merge_entry(consequences, data, seen_hashes):
        consequences.append(data)
    
    def read_all(self) -> List[Dict[str, Any]]:
        return self._read_all()
    
    def _read_all(self):
        seen_hashes: Dict[str, float] = {}  # hash -> timestamp
        consequences = []
        
        for loc in MockConsequenceSystem.STORAGE_LOCATIONS:
            filepath = os.path.join(loc, self._storage_name)
            if not os.path.exists(filepath):
                continue
                
            location_consequences = self._read_from_file(filepath)
            for data in location_consequences:
                self._merge_entry(consequences, data, seen_hashes)
        
        return consequences

@pytest.fixture
def mock_consequence_system():
    return MockConsequenceSystem('test_storage')

def test_read_all_happy_path(mock_consequence_system):
    result = mock_consequence_system.read_all()
    assert len(result) == 2
    assert all(isinstance(item, dict) for item in result)
    assert 'hash' in result[0]
    assert 'data' in result[0]

def test_read_all_empty_locations(mock_consequence_system):
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = False
        result = mock_consequence_system.read_all()
        assert len(result) == 0

def test_read_all_with_error(mock_consequence_system):
    with patch('os.listdir', side_effect=FileNotFoundError):
        result = mock_consequence_system.read_all()
        assert len(result) == 0