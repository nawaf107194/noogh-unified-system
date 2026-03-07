import pytest
import os
from unittest.mock import patch, MagicMock

class MockSnapshotDB:
    def __init__(self, snapshot_dir):
        self.snapshot_dir = snapshot_dir

    @patch('os.listdir')
    def test_load_latest_snapshot_happy_path(self, mock_listdir):
        # Arrange
        snapshot_dir = 'test_snapshots'
        os.makedirs(snapshot_dir, exist_ok=True)
        snapshot_files = ['snapshot_1.json', 'snapshot_2.json']
        for file in snapshot_files:
            with open(os.path.join(snapshot_dir, file), 'w') as f:
                json.dump({'key': 'value'}, f)
        
        mock_listdir.return_value = snapshot_files
        db_instance = MockSnapshotDB(snapshot_dir)

        # Act
        result = db_instance.load_latest_snapshot()

        # Assert
        assert result == {'key': 'value'}
        assert os.path.join(snapshot_dir, 'snapshot_2.json') in open(mock_listdir.call_args[0][0]).readlines()

    @patch('os.listdir')
    def test_load_latest_snapshot_edge_case_empty_directory(self, mock_listdir):
        # Arrange
        snapshot_dir = 'test_snapshots'
        os.makedirs(snapshot_dir, exist_ok=True)
        mock_listdir.return_value = []
        db_instance = MockSnapshotDB(snapshot_dir)

        # Act & Assert
        with pytest.raises(FileNotFoundError) as excinfo:
            db_instance.load_latest_snapshot()
        assert str(excinfo.value) == "No snapshots found"

    @patch('os.listdir')
    def test_load_latest_snapshot_edge_case_nonexistent_directory(self, mock_listdir):
        # Arrange
        snapshot_dir = 'nonexistent_snapshots'
        mock_listdir.return_value = []
        db_instance = MockSnapshotDB(snapshot_dir)

        # Act & Assert
        with pytest.raises(FileNotFoundError) as excinfo:
            db_instance.load_latest_snapshot()
        assert str(excinfo.value) == "No snapshots found"

    @patch('os.listdir')
    def test_load_latest_snapshot_async_behavior(self, mock_listdir):
        # Arrange
        snapshot_dir = 'test_snapshots'
        os.makedirs(snapshot_dir, exist_ok=True)
        snapshot_files = ['snapshot_1.json', 'snapshot_2.json']
        for file in snapshot_files:
            with open(os.path.join(snapshot_dir, file), 'w') as f:
                json.dump({'key': 'value'}, f)

        mock_listdir.return_value = snapshot_files
        db_instance = MockSnapshotDB(snapshot_dir)

        # Act & Assert (asynchronous behavior is not explicitly handled in the code)
        result = db_instance.load_latest_snapshot()
        assert result == {'key': 'value'}