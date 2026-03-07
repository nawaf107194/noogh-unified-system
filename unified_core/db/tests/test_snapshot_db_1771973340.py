import pytest
import os
import json
from unified_core.db.snapshot_db_1771973340 import SnapshotDB

# Mocking the SnapshotDB class for testing
class MockSnapshotDB:
    def __init__(self, snapshot_dir):
        self.snapshot_dir = snapshot_dir

@pytest.fixture
def mock_snapshot_db():
    with tempfile.TemporaryDirectory() as tempdir:
        yield MockSnapshotDB(tempdir)

def test_load_latest_snapshot_happy_path(mock_snapshot_db):
    os.makedirs(os.path.join(mock_snapshot_db.snapshot_dir, 'snapshot_2023-04-01T12:00:00.000Z'))
    os.makedirs(os.path.join(mock_snapshot_db.snapshot_dir, 'snapshot_2023-04-02T12:00:00.000Z'))
    snapshot_path = os.path.join(mock_snapshot_db.snapshot_dir, 'snapshot_2023-04-02T12:00:00.000Z', 'data.json')
    with open(snapshot_path, 'w') as f:
        json.dump({'key': 'value'}, f)

    db = SnapshotDB(mock_snapshot_db.snapshot_dir)
    result = db.load_latest_snapshot()

    assert result == {'key': 'value'}
    assert os.path.basename(result['path']) == 'snapshot_2023-04-02T12:00:00.000Z'

def test_load_latest_snapshot_empty_folder(mock_snapshot_db):
    with pytest.raises(FileNotFoundError):
        db = SnapshotDB(mock_snapshot_db.snapshot_dir)
        db.load_latest_snapshot()

def test_load_latest_snapshot_nonexistent_directory():
    non_existent_dir = '/path/to/nonexistent/directory'
    db = SnapshotDB(non_existent_dir)
    with pytest.raises(FileNotFoundError):
        db.load_latest_snapshot()