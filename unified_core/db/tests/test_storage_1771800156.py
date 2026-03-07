import pytest
from unittest.mock import patch, mock_open
from datetime import datetime
import os
import shutil

from unified_core.db.storage_1771800156 import Storage

def test_save_snapshot_happy_path(tmpdir):
    storage = Storage(root_dir=str(tmpdir))
    
    with patch("datetime.datetime.now") as MockDateTime:
        MockDateTime.return_value = datetime(2023, 10, 1, 12, 0, 0)
        
        snapshot_path = os.path.join(str(tmpdir), "snapshot_20231001120000")
        with patch("shutil.copytree") as MockCopyTree:
            storage.save_snapshot()
            
            MockCopyTree.assert_called_once_with(".", snapshot_path)
            assert os.path.exists(snapshot_path)

def test_save_snapshot_edge_cases(tmpdir):
    storage = Storage(root_dir=str(tmpdir))
    
    # Edge case: empty root_dir
    with pytest.raises(ValueError, match="Root directory cannot be empty"):
        storage.root_dir = ""
        storage.save_snapshot()
        
    # Edge case: None root_dir
    with pytest.raises(ValueError, match="Root directory cannot be None"):
        storage.root_dir = None
        storage.save_snapshot()

def test_save_snapshot_error_cases(tmpdir):
    storage = Storage(root_dir=str(tmpdir))
    
    # Error case: invalid root_dir (non-existent directory)
    with pytest.raises(FileNotFoundError, match="No such file or directory"):
        storage.root_dir = "/path/to/non_existent_directory"
        storage.save_snapshot()
        
def test_save_snapshot_async_behavior():
    # Since the function is synchronous and does not contain any async code,
    # there is no need to test for async behavior.
    pass