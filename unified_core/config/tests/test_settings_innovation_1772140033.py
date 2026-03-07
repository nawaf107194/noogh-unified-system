import pytest
from pathlib import Path

def _get_tiered_locations(primary_dir: Path, backup_dir: Path, legacy_user_path: str = None) -> List[str]:
    locs = [
        str(primary_dir),
        str(backup_dir),
        "/tmp/.noogh_emergency"
    ]
    if legacy_user_path and legacy_user_path.strip():  # Check if legacy_user_path exists and is not empty
        locs.append(legacy_user_path)
    return locs

def test_get_tiered_locations_happy_path():
    primary = Path("/mnt/data")
    backup = Path("/backup/data")
    result = _get_tiered_locations(primary, backup)
    expected = [str(primary), str(backup), "/tmp/.noogh_emergency"]
    assert result == expected

def test_get_tiered_locations_empty_paths():
    primary = Path("")
    backup = Path("")
    result = _get_tiered_locations(primary, backup)
    expected = ["", "", "/tmp/.noogh_emergency"]
    assert result == expected

def test_get_tiered_locations_none_paths():
    primary = None
    backup = None
    result = _get_tiered_locations(primary, backup)
    expected = [None, None, "/tmp/.noogh_emergency"]
    assert result == expected

def test_get_tiered_locations_with_legacy_path():
    primary = Path("/mnt/data")
    backup = Path("/backup/data")
    legacy = "/home/user/legacy"
    result = _get_tiered_locations(primary, backup, legacy)
    expected = [str(primary), str(backup), "/tmp/.noogh_emergency", legacy]
    assert result == expected

def test_get_tiered_locations_empty_legacy_path():
    primary = Path("/mnt/data")
    backup = Path("/backup/data")
    legacy = ""
    result = _get_tiered_locations(primary, backup, legacy)
    expected = [str(primary), str(backup), "/tmp/.noogh_emergency"]
    assert result == expected

def test_get_tiered_locations_none_legacy_path():
    primary = Path("/mnt/data")
    backup = Path("/backup/data")
    legacy = None
    result = _get_tiered_locations(primary, backup, legacy)
    expected = [str(primary), str(backup), "/tmp/.noogh_emergency"]
    assert result == expected

def test_get_tiered_locations_invalid_primary_path():
    primary = "invalid/path"
    backup = Path("/backup/data")
    with pytest.raises(ValueError):
        _get_tiered_locations(primary, backup)

def test_get_tiered_locations_invalid_backup_path():
    primary = Path("/mnt/data")
    backup = "invalid/path"
    with pytest.raises(ValueError):
        _get_tiered_locations(primary, backup)