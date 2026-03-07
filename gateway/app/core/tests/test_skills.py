import pytest
from unittest.mock import Mock
from gateway.app.core.skills import Skills  # Adjust the import according to your module structure

@pytest.fixture
def skills_instance():
    instance = Skills()
    instance.safe_root = "/safe/root"
    return instance

def test_ensure_safe_path_happy_path(skills_instance):
    assert skills_instance._ensure_safe_path("subdir") == "/safe/root/subdir"
    assert skills_instance._ensure_safe_path("/safe/root/another_subdir") == "/safe/root/another_subdir"

def test_ensure_safe_path_empty_path(skills_instance):
    assert skills_instance._ensure_safe_path("") == "/safe/root/"

def test_ensure_safe_path_none_path(skills_instance):
    assert skills_instance._ensure_safe_path(None) == "/safe/root/"

def test_ensure_safe_path_outside_root(skills_instance):
    with pytest.raises(ValueError) as excinfo:
        skills_instance._ensure_safe_path("/outside/root")
    assert "is outside of SAFE_ROOT" in str(excinfo.value)

def test_ensure_safe_path_parent_dir_traversal(skills_instance):
    with pytest.raises(ValueError) as excinfo:
        skills_instance._ensure_safe_path("../unsafe/path")
    assert "is outside of SAFE_ROOT" in str(excinfo.value)

def test_ensure_safe_path_absolute_path_within_root(skills_instance):
    assert skills_instance._ensure_safe_path("/safe/root/subdir") == "/safe/root/subdir"

def test_ensure_safe_path_relative_path_within_root(skills_instance):
    assert skills_instance._ensure_safe_path("subdir") == "/safe/root/subdir"

def test_ensure_safe_path_root_itself(skills_instance):
    assert skills_instance._ensure_safe_path("/") == "/safe/root"

def test_ensure_safe_path_with_dot(skills_instance):
    assert skills_instance._ensure_safe_path(".") == "/safe/root"

def test_ensure_safe_path_with_double_dots(skills_instance):
    assert skills_instance._ensure_safe_path("..") == "/safe/root"

def test_ensure_safe_path_with_tilde(skills_instance):
    with pytest.raises(ValueError) as excinfo:
        skills_instance._ensure_safe_path("~/Documents")
    assert "is outside of SAFE_ROOT" in str(excinfo.value)

def test_ensure_safe_path_with_special_characters(skills_instance):
    assert skills_instance._ensure_safe_path("subdir!@#$%^&*()") == "/safe/root/subdir!@#$%^&*()"