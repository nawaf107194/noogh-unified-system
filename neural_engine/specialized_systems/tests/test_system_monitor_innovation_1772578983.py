import pytest
from unittest.mock import patch
from neural_engine.specialized_systems.system_monitor import FileManager

def test_filemanager_init_happy_path():
    """Test FileManager initialization with normal inputs"""
    with patch('neural_engine.specialized_systems.system_monitor.logger') as mock_logger:
        # Create instance
        file_manager = FileManager()
        
        # Verify logger was called
        mock_logger.info.assert_called_once_with("FileManager initialized")

def test_filemanager_init_multiple_instances():
    """Test FileManager initialization with multiple instances"""
    with patch('neural_engine.specialized_systems.system_monitor.logger') as mock_logger:
        # Create multiple instances
        file_manager1 = FileManager()
        file_manager2 = FileManager()
        
        # Verify logger was called twice
        assert mock_logger.info.call_count == 2
        mock_logger.info.assert_has_calls([
            pytest.mock.call("FileManager initialized"),
            pytest.mock.call("FileManager initialized")
        ])