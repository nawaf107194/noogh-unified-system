import pytest
from pathlib import Path
import os

@pytest.fixture
def allowed_roots(tmp_path):
    # Create test allowed roots
    allowed1 = tmp_path / "allowed_root1"
    allowed2 = tmp_path / "allowed_root2"
    allowed1.mkdir()
    allowed2.mkdir()
    return [allowed1, allowed2]

def test_is_path_safe_valid_path(allowed_roots):
    # Test valid path within allowed roots
    test_path = str(allowed_roots[0] / "subdir" / "file.txt")
    assert _is_path_safe(test_path) is True

def test_is_path_safe_outside_allowed(allowed_roots):
    # Test path outside allowed roots
    test_path = str(allowed_roots[0].parent / "outside" / "file.txt")
    assert _is_path_safe(test_path) is False

def test_is_path_safe_empty_string():
    # Test empty string input
    assert _is_path_safe("") is False

def test_is_path_safe_none_input():
    # Test None input
    assert _is_path_safe(None) is False

def test_is_path_safe_symlink(allowed_roots, tmp_path):
    # Test symlink to allowed path
    test_path = tmp_path / "symlink"
    os.symlink(str(allowed_roots[0] / "subdir"), str(test_path))
    assert _is_path_safe(str(test_path)) is True

def test_is_path_safe_windows_style_path(allowed_roots):
    # Test Windows-style path
    test_path = os.path.join(str(allowed_roots[0]), "subdir", "file.txt")
    assert _is_path_safe(test_path) is True

def test_is_path_safe_relative_path(allowed_roots):
    # Test relative path that resolves to allowed root
    os.chdir(str(allowed_roots[0]))
    test_path = "./subdir/file.txt"
    assert _is_path_safe(test_path) is True