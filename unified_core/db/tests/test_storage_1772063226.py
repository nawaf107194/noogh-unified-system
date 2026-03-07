import pytest
from unified_core.db.storage_1772063226 import get_latest_snapshot, Snapshot

def mock_load_snapshot(file_path):
    return Snapshot(version=int(file_path.split('.')[0]), data={})

@pytest.fixture(autouse=True)
def patch_load_snapshot(monkeypatch):
    monkeypatch.setattr('unified_core.db.storage_1772063226.load_snapshot', mock_load_snapshot)

def test_get_latest_snapshot_happy_path():
    with pytest.raises(FileNotFoundError):
        get_latest_snapshot("/path/to/empty/directory")

def test_get_latest_snapshot_empty_directory():
    import os
    with pytest.raises(FileNotFoundError) as exc_info:
        get_latest_snapshot("/path/to/empty/directory")
    assert "No JSON snapshot files found" in str(exc_info.value)

def test_get_latest_snapshot_none_directory():
    with pytest.raises(TypeError) as exc_info:
        get_latest_snapshot(None)
    assert "Directory must be a string" in str(exc_info.value)

def test_get_latest_snapshot_boundary_case():
    import os
    os.makedirs("/path/to/one/snapshot", exist_ok=True)
    open(os.path.join("/path/to/one/snapshot", "1.json"), 'w').close()
    snapshot = get_latest_snapshot("/path/to/one/snapshot")
    assert isinstance(snapshot, Snapshot)
    assert snapshot.version == 1

def test_get_latest_snapshot_multiple_snapshots():
    import os
    os.makedirs("/path/to/multiple/snapshots", exist_ok=True)
    for i in range(5):
        open(os.path.join("/path/to/multiple/snapshots", f"{i}.json"), 'w').close()
    snapshot = get_latest_snapshot("/path/to/multiple/snapshots")
    assert isinstance(snapshot, Snapshot)
    assert snapshot.version == 4