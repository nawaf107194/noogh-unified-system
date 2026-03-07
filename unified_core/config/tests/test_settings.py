import pytest
from unittest.mock import MagicMock
from pathlib import Path
from typing import List
from noogh_unified_system.src.unified_core.config.settings import _get_tiered_locations

@pytest.fixture
def mock_paths():
    primary_dir = Path("/path/to/primary")
    backup_dir = Path("/path/to/backup")
    return primary_dir, backup_dir

def test_happy_path(mock_paths):
    primary_dir, backup_dir = mock_paths
    expected = ["/path/to/primary", "/path/to/backup", "/tmp/.noogh_emergency"]
    result = _get_tiered_locations(primary_dir, backup_dir)
    assert result == expected

def test_empty_input(mock_paths):
    primary_dir, backup_dir = mock_paths
    expected = ["/path/to/primary", "/path/to/backup", "/tmp/.noogh_emergency"]
    result = _get_tiered_locations(primary_dir, backup_dir, "")
    assert result == expected

def test_none_input(mock_paths):
    primary_dir, backup_dir = mock_paths
    expected = ["/path/to/primary", "/path/to/backup", "/tmp/.noogh_emergency"]
    result = _get_tiered_locations(primary_dir, backup_dir, None)
    assert result == expected

def test_invalid_input(mock_paths):
    primary_dir, backup_dir = mock_paths
    with pytest.raises(TypeError):
        _get_tiered_locations("not/a/path", "also/not/a/path")

def test_legacy_user_path(mock_paths):
    primary_dir, backup_dir = mock_paths
    legacy_path = "/legacy/path"
    expected = ["/path/to/primary", "/path/to/backup", "/tmp/.noogh_emergency", legacy_path]
    result = _get_tiered_locations(primary_dir, backup_dir, legacy_path)
    assert result == expected

def test_async_behavior(mock_paths):
    # Since the function does not involve async operations, this test is not applicable.
    pass