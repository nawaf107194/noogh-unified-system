import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
from noogh_unified_system.src.unified_core.evolution.architecture_model import ArchitectureModel

def test_load_cache_happy_path(mocker):
    # Mock the necessary attributes and methods
    model = ArchitectureModel()
    model._cache_file = Path("test_cache.json")
    
    mock_data = {
        "scan_time": 12345,
        "scan_count": 67890,
        "nodes": {}
    }
    
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.return_value = json.dumps(mock_data)
        
        # Call the method to test
        result = model.load_cache()
        
        # Assertions
        assert result is True
        mock_open.assert_called_once_with(model._cache_file, 'r')
        mock_file.read.assert_called_once()
        assert model._last_full_scan == 12345
        assert model._scan_count == 67890
        logger.info.assert_called_once_with(
            "🏗️ Architecture model loaded from cache (0 components)"
        )

def test_load_cache_cache_file_not_exists(mocker):
    # Mock the necessary attributes and methods
    model = ArchitectureModel()
    model._cache_file = Path("nonexistent_cache.json")
    
    with patch('builtins.open', side_effect=FileNotFoundError) as mock_open:
        # Call the method to test
        result = model.load_cache()
        
        # Assertions
        assert result is False
        mock_open.assert_called_once_with(model._cache_file, 'r')
        logger.warning.assert_called_once_with("Failed to load arch cache: [Errno 2] No such file or directory: 'nonexistent_cache.json'")

def test_load_cache_invalid_json(mocker):
    # Mock the necessary attributes and methods
    model = ArchitectureModel()
    model._cache_file = Path("invalid_json_cache.json")
    
    mock_data = "not valid json"
    
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.return_value = mock_data
        
        # Call the method to test
        result = model.load_cache()
        
        # Assertions
        assert result is False
        mock_open.assert_called_once_with(model._cache_file, 'r')
        mock_file.read.assert_called_once()
        logger.warning.assert_called_once_with("Failed to load arch cache: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)")

def test_load_cache_logger(mocker):
    # Mock the necessary attributes and methods
    model = ArchitectureModel()
    model._cache_file = Path("test_cache.json")
    
    mock_data = {
        "scan_time": 12345,
        "scan_count": 67890,
        "nodes": {}
    }
    
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.return_value = json.dumps(mock_data)
        
        # Mock the logger to capture info messages
        with patch.object(model, '_log') as mock_logger:
            # Call the method to test
            result = model.load_cache()
            
            # Assertions
            assert result is True
            mock_open.assert_called_once_with(model._cache_file, 'r')
            mock_file.read.assert_called_once()
            mock_logger.info.assert_called_once_with(
                "🏗️ Architecture model loaded from cache (0 components)"
            )