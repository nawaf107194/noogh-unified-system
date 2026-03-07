import os
from datetime import datetime, timedelta
from unittest.mock import patch

from unified_core.db.backup_rotation import rotate_backups

def test_happy_path(monkeypatch):
    backup_folder = '/tmp/test_backup'
    max_days = 30
    
    # Create some mock backup files
    now = datetime.now()
    two_months_ago = now - timedelta(days=60)
    one_month_ago = now - timedelta(days=31)
    
    file_names = [
        f"backup_{two_months_ago.strftime('%Y-%m-%d')}.sqlite",
        f"backup_{one_month_ago.strftime('%Y-%m-%d')}.sqlite",
        "backup_recent.sqlite"
    ]
    
    with patch.dict('os.listdir', return_value=file_names):
        with patch.object(os, 'remove') as mock_remove:
            rotate_backups(backup_folder, max_days)
            
            # Check that only the old files were removed
            assert mock_remove.call_count == 2
            for call_args in mock_remove.call_args_list:
                assert backup_folder + '/' + f"backup_{two_months_ago.strftime('%Y-%m-%d')}.sqlite" not in call_args[0]
                assert backup_folder + '/' + f"backup_{one_month_ago.strftime('%Y-%m-%d')}.sqlite" in call_args[0]

def test_empty_backup_folder(monkeypatch):
    backup_folder = '/tmp/test_backup'
    
    with patch.dict('os.listdir', return_value=[]):
        rotate_backups(backup_folder)
        
        # No files should be removed
        assert not os.listdir(backup_folder)

def test_none_backup_folder():
    with pytest.raises(TypeError):
        rotate_backups(None)

def test_invalid_max_days():
    backup_folder = '/tmp/test_backup'
    
    with pytest.raises(ValueError) as exc_info:
        rotate_backups(backup_folder, max_days=-1)
        
    assert str(exc_info.value) == "max_days must be a non-negative integer"

def test_async_behavior(monkeypatch):
    async def mock_listdir(path):
        return ["backup_2023-04-01.sqlite", "backup_2023-05-01.sqlite"]
    
    async def mock_remove(path):
        pass
    
    backup_folder = '/tmp/test_backup'
    max_days = 30
    
    with patch('unified_core.db.backup_rotation.asyncio', autospec=True) as mock_asyncio:
        mock_asyncio.run.side_effect = [mock_listdir, mock_remove]
        
        rotate_backups(backup_folder, max_days)
        
        # Check that only the old files were removed
        assert mock_asyncio.run.call_count == 2
        for call_args in mock_asyncio.run.call_args_list:
            assert backup_folder + '/' + f"backup_2023-04-01.sqlite" not in call_args[0]
            assert backup_folder + '/' + f"backup_2023-05-01.sqlite" in call_args[0]