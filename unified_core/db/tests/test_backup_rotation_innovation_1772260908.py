import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import os

def test_rotate_backups_happy_path():
    backup_folder = "/tmp/test_backup"
    max_days = 30
    
    # Create mock files in the backup folder
    file_names = [
        "backup_2023-01-01.sqlite",
        "backup_2023-02-01.sqlite",
        "backup_2023-03-01.sqlite"
    ]
    
    with patch("os.listdir", return_value=file_names), \
         patch("os.path.join") as mock_join, \
         patch("datetime.datetime.now", return_value=datetime(2023, 4, 1)):
        
        rotate_backups(backup_folder, max_days)
        
        # Check if the files were deleted correctly
        assert not any(file_name.startswith("backup_2023-01-01") for file_name in os.listdir(backup_folder))
        assert file_name.startswith("backup_2023-02-01")
        assert file_name.startswith("backup_2023-03-01")

def test_rotate_backups_empty_folder():
    backup_folder = "/tmp/test_backup"
    
    with patch("os.listdir", return_value=[]):
        rotate_backups(backup_folder)
        
        # Check if any files were deleted
        assert not os.listdir(backup_folder)

def test_rotate_backups_none_input():
    backup_folder = None
    
    with pytest.raises(TypeError) as exc_info:
        rotate_backups(backup_folder)
    
    assert "backup_folder" in str(exc_info.value)

def test_rotate_backups_invalid_date_format():
    backup_folder = "/tmp/test_backup"
    
    # Create a mock file with an invalid date format
    file_names = [
        "backup_2023-01-01.sqlite",
        "backup_2023-02-30.sqlite"
    ]
    
    with patch("os.listdir", return_value=file_names), \
         patch("datetime.datetime.strptime", side_effect=ValueError):
        
        rotate_backups(backup_folder)
        
        # Check if the files were not deleted
        assert any(file_name.startswith("backup_2023-01-01") for file_name in os.listdir(backup_folder))
        assert any(file_name.startswith("backup_2023-02-30") for file_name in os.listdir(backup_folder))

def test_rotate_backups_max_days_boundary():
    backup_folder = "/tmp/test_backup"
    max_days = 1
    
    # Create mock files in the backup folder
    file_names = [
        "backup_2023-03-30.sqlite",
        "backup_2023-04-01.sqlite"
    ]
    
    with patch("os.listdir", return_value=file_names), \
         patch("datetime.datetime.now", return_value=datetime(2023, 4, 1)):
        
        rotate_backups(backup_folder, max_days)
        
        # Check if the files were deleted correctly
        assert not any(file_name.startswith("backup_2023-03-30") for file_name in os.listdir(backup_folder))
        assert file_name.startswith("backup_2023-04-01")