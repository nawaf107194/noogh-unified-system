import pytest
from datetime import datetime, timedelta
import os

from unified_core.db.backup_rotation import _build_backup_path

def test_happy_path():
    base_path = "/path/to/backups"
    expected_output = os.path.join(base_path, f"backup_{datetime.now().strftime('%Y-%m-%d')}.sqlite")
    assert _build_backup_path(base_path) == expected_output

def test_edge_case_empty_base_path():
    base_path = ""
    expected_output = f"backup_{datetime.now().strftime('%Y-%m-%d')}.sqlite"
    assert _build_backup_path(base_path) == expected_output

def test_edge_case_none_base_path():
    base_path = None
    with pytest.raises(TypeError):
        _build_backup_path(base_path)

def test_error_case_invalid_base_path_type():
    with pytest.raises(TypeError):
        _build_backup_path(123)