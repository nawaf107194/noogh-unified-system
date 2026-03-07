import pytest
import os

from unified_core.db.storage_1771800156 import Storage

def test_init_happy_path(tmpdir):
    root_dir = str(tmpdir)
    storage = Storage(root_dir)
    assert storage.root_dir == root_dir
    assert os.path.exists(root_dir)

def test_init_edge_case_empty_root_dir():
    root_dir = ""
    with pytest.raises(ValueError, match="root_dir cannot be empty"):
        Storage(root_dir)

def test_init_edge_case_none_root_dir():
    root_dir = None
    with pytest.raises(ValueError, match="root_dir cannot be None"):
        Storage(root_dir)

def test_init_error_case_invalid_root_dir(tmpdir):
    invalid_root_dir = str(tmpdir) + "invalid"
    storage = Storage(invalid_root_dir)
    assert os.path.exists(invalid_root_dir)

# Async behavior is not applicable for this function