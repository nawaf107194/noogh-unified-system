import pytest
from pathlib import Path
from unified_core.config.settings import _get_tiered_locations

def test_get_tiered_locations_happy_path():
    primary_dir = Path("/home/user/data")
    backup_dir = Path("/backup/data")
    expected_result = [str(primary_dir), str(backup_dir), "/tmp/.noogh_emergency"]
    assert _get_tiered_locations(primary_dir, backup_dir) == expected_result

def test_get_tiered_locations_with_legacy_user_path():
    primary_dir = Path("/home/user/data")
    backup_dir = Path("/backup/data")
    legacy_user_path = "/home/user/old_data"
    expected_result = [str(primary_dir), str(backup_dir), "/tmp/.noogh_emergency", legacy_user_path]
    assert _get_tiered_locations(primary_dir, backup_dir, legacy_user_path) == expected_result

def test_get_tiered_locations_with_empty_primary_dir():
    primary_dir = Path("")
    backup_dir = Path("/backup/data")
    expected_result = ["", str(backup_dir), "/tmp/.noogh_emergency"]
    assert _get_tiered_locations(primary_dir, backup_dir) == expected_result

def test_get_tiered_locations_with_none_primary_dir():
    primary_dir = None
    backup_dir = Path("/backup/data")
    expected_result = [None, str(backup_dir), "/tmp/.noogh_emergency"]
    assert _get_tiered_locations(primary_dir, backup_dir) == expected_result

def test_get_tiered_locations_with_empty_backup_dir():
    primary_dir = Path("/home/user/data")
    backup_dir = Path("")
    expected_result = [str(primary_dir), "", "/tmp/.noogh_emergency"]
    assert _get_tiered_locations(primary_dir, backup_dir) == expected_result

def test_get_tiered_locations_with_none_backup_dir():
    primary_dir = Path("/home/user/data")
    backup_dir = None
    expected_result = [str(primary_dir), None, "/tmp/.noogh_emergency"]
    assert _get_tiered_locations(primary_dir, backup_dir) == expected_result

def test_get_tiered_locations_with_invalid_primary_dir():
    primary_dir = "not_a_path"
    backup_dir = Path("/backup/data")
    expected_result = ["not_a_path", str(backup_dir), "/tmp/.noogh_emergency"]
    assert _get_tiered_locations(primary_dir, backup_dir) == expected_result

def test_get_tiered_locations_with_invalid_backup_dir():
    primary_dir = Path("/home/user/data")
    backup_dir = "not_a_path"
    expected_result = [str(primary_dir), "not_a_path", "/tmp/.noogh_emergency"]
    assert _get_tiered_locations(primary_dir, backup_dir) == expected_result

def test_get_tiered_locations_with_no_params():
    primary_dir = None
    backup_dir = None
    expected_result = [None, None, "/tmp/.noogh_emergency"]
    assert _get_tiered_locations(primary_dir, backup_dir) == expected_result