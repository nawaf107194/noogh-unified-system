import pytest
from pathlib import Path
from noogh_unified_system.src.gateway.app.core.persistent_memory import PersistentMemory

def test_init_happy_path(tmp_path):
    storage_dir = tmp_path / "test_storage"
    pm = PersistentMemory(storage_dir)
    assert isinstance(pm.storage_path, Path)
    assert pm.storage_path.exists()
    assert pm.tasks_file.exists()
    assert pm.conversations_file.exists()
    assert logger.info.call_args_list == [call("Persistent memory initialized: %s", storage_dir)]

def test_init_edge_case_empty_string():
    with pytest.raises(ValueError) as exc_info:
        PersistentMemory("")
    assert str(exc_info.value) == "storage_dir cannot be empty"

def test_init_edge_case_none():
    with pytest.raises(ValueError) as exc_info:
        PersistentMemory(None)
    assert str(exc_info.value) == "storage_dir cannot be None"

def test_init_error_case_invalid_path(tmp_path):
    invalid_storage_dir = tmp_path / "nonexistent" / "dir"
    pm = PersistentMemory(invalid_storage_dir)
    assert isinstance(pm.storage_path, Path)
    assert not pm.storage_path.exists()
    assert pm.tasks_file.exists() is False
    assert pm.conversations_file.exists() is False

# Assuming logger.info is patched to capture calls
@pytest.mark.parametrize("storage_dir", ["", None])
def test_init_edge_cases_logger(tmp_path, storage_dir):
    with pytest.raises(ValueError) as exc_info:
        PersistentMemory(storage_dir)
    assert logger.info.call_args_list == []

@pytest.mark.asyncio
async def test_async_init_happy_path(tmp_path):
    storage_dir = tmp_path / "test_storage"
    pm = PersistentMemory(storage_dir)
    assert isinstance(pm.storage_path, Path)
    assert pm.storage_path.exists()
    assert pm.tasks_file.exists()
    assert pm.conversations_file.exists()

@pytest.mark.asyncio
async def test_async_init_edge_case_empty_string():
    with pytest.raises(ValueError) as exc_info:
        await PersistentMemory("")
    assert str(exc_info.value) == "storage_dir cannot be empty"

@pytest.mark.asyncio
async def test_async_init_edge_case_none():
    with pytest.raises(ValueError) as exc_info:
        await PersistentMemory(None)
    assert str(exc_info.value) == "storage_dir cannot be None"