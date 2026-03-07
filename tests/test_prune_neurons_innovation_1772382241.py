import pytest
from prune_neurons import load_fabric, FABRIC_PATH

def test_load_fabric_happy_path(mocker):
    """Test normal inputs."""
    mock_data = {"neurons": []}
    mocker.patch.object(json, 'load', return_value=mock_data)
    
    result = load_fabric()
    assert result == mock_data

def test_load_fabric_edge_case_empty_file(mocker):
    """Test edge case: empty file."""
    mocker.patch.object(json, 'load', side_effect=json.JSONDecodeError("Expecting value", pos=0))
    
    result = load_fabric()
    assert result is None

def test_load_fabric_edge_case_none_file(mocker):
    """Test edge case: non-existent file."""
    mocker.patch('builtins.open', side_effect=FileNotFoundError)
    
    result = load_fabric()
    assert result is None