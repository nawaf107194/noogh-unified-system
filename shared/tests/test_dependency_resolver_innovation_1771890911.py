import pytest
from shared.dependency_resolver import load_module

def test_load_module_happy_path():
    """Test loading a valid module."""
    load_module("math")
    # If no assertion is raised, it means the module was loaded successfully

def test_load_module_empty_input():
    """Test loading an empty string as module name."""
    with pytest.raises(SystemExit) as exc_info:
        load_module("")
    assert "Failed to load module : No module named ''" in str(exc_info.value)

def test_load_module_none_input():
    """Test loading None as module name."""
    with pytest.raises(SystemExit) as exc_info:
        load_module(None)
    assert "Failed to load module : None is not a valid string" in str(exc_info.value)

def test_load_module_invalid_input():
    """Test loading an invalid module name."""
    with pytest.raises(SystemExit) as exc_info:
        load_module("nonexistentmodule")
    assert "Failed to load module nonexistentmodule: No module named 'nonexistentmodule'" in str(exc_info.value)