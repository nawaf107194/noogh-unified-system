import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json

from unified_core.db.snapshot_db import SnapshotDB

@pytest.fixture
def snapshot_db():
    return SnapshotDB()

@patch('unified_core.db.snapshot_db.datetime.now')
@patch('unified_core.db.snapshot_db.open')
def test_save_snapshot_happy_path(mock_open, mock_datetime, snapshot_db):
    system_state = {'key': 'value'}
    timestamp = '20231005123456'
    mock_datetime.now.return_value.strftime.return_value = timestamp

    snapshot_db.save_snapshot(system_state)

    mock_open.assert_called_once_with(f'/path/to/snapshots/snapshot_{timestamp}.json', 'w')
    mock_open().__enter__().write.assert_called_once_with(json.dumps(system_state))
    print_statement = capsys.readouterr().out
    assert "Snapshot saved to /path/to/snapshots/snapshot_20231005123456.json" in print_statement

@patch('unified_core.db.snapshot_db.datetime.now')
def test_save_snapshot_no_system_state(mock_datetime, snapshot_db):
    timestamp = '20231005123456'
    mock_datetime.now.return_value.strftime.return_value = timestamp
    snapshot_db.db_manager.get_system_state.return_value = {'key': 'value'}

    snapshot_db.save_snapshot()

    with open(f'/path/to/snapshots/snapshot_{timestamp}.json', 'r') as file:
        content = json.load(file)
    assert content == {'key': 'value'}
    print_statement = capsys.readouterr().out
    assert "Snapshot saved to /path/to/snapshots/snapshot_20231005123456.json" in print_statement

def test_save_snapshot_empty_system_state(snapshot_db):
    snapshot_db.db_manager.get_system_state.return_value = {}

    with patch('unified_core.db.snapshot_db.datetime.now', return_value=datetime(2023, 10, 5, 12, 34, 56)):
        snapshot_db.save_snapshot()

    with open(f'/path/to/snapshots/snapshot_20231005123456.json', 'r') as file:
        content = json.load(file)
    assert content == {}

def test_save_snapshot_none_system_state(snapshot_db):
    snapshot_db.db_manager.get_system_state.return_value = None

    with patch('unified_core.db.snapshot_db.datetime.now', return_value=datetime(2023, 10, 5, 12, 34, 56)):
        snapshot_db.save_snapshot()

    with open(f'/path/to/snapshots/snapshot_20231005123456.json', 'r') as file:
        content = json.load(file)
    assert content == {}

def test_save_snapshot_invalid_system_state(snapshot_db):
    invalid_state = {'key': ['value', None, 'another_value']}
    snapshot_db.db_manager.get_system_state.return_value = invalid_state

    with patch('unified_core.db.snapshot_db.datetime.now', return_value=datetime(2023, 10, 5, 12, 34, 56)):
        snapshot_db.save_snapshot()

    with open(f'/path/to/snapshots/snapshot_20231005123456.json', 'r') as file:
        content = json.load(file)
    assert content == {'key': ['value', None, 'another_value']}