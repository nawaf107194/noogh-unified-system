import pytest
from unified_core.core.coercive_memory import _deprecated_alias

def test_deprecated_alias_happy_path(monkeypatch):
    # Mock the environment variable to simulate strict mode off
    monkeypatch.setenv("NOOGH_STRICT_MODE", "0")
    
    # Define old_name, new_name, and new_class for testing
    old_name = "old_function"
    new_name = "new_function"
    class NewClass:
        pass
    
    # Call the function
    result = _deprecated_alias(old_name, new_name, NewClass)
    
    # Assert that the result is the new_class
    assert result == NewClass

def test_deprecated_alias_strict_mode_on(monkeypatch):
    # Mock the environment variable to simulate strict mode on
    monkeypatch.setenv("NOOGH_STRICT_MODE", "1")
    
    # Define old_name, new_name, and new_class for testing
    old_name = "old_function"
    new_name = "new_function"
    class NewClass:
        pass
    
    with pytest.raises(RuntimeError) as exc_info:
        _deprecated_alias(old_name, new_name, NewClass)
    
    assert str(exc_info.value) == f"{old_name} is deprecated. Use {new_name}. This alias will be removed."

def test_deprecated_alias_empty_old_name(monkeypatch):
    # Mock the environment variable to simulate strict mode off
    monkeypatch.setenv("NOOGH_STRICT_MODE", "0")
    
    # Define old_name, new_name, and new_class for testing
    old_name = ""
    new_name = "new_function"
    class NewClass:
        pass
    
    with pytest.warns(DeprecationWarning) as warning_info:
        result = _deprecated_alias(old_name, new_name, NewClass)
    
    # Assert that the result is the new_class
    assert result == NewClass
    
    # Check the warning message
    assert str(warning_info[0].message) == f"{old_name} is deprecated. Use {new_name}. This alias will be removed."

def test_deprecated_alias_none_new_name(monkeypatch):
    # Mock the environment variable to simulate strict mode off
    monkeypatch.setenv("NOOGH_STRICT_MODE", "0")
    
    # Define old_name, new_name, and new_class for testing
    old_name = "old_function"
    new_name = None
    class NewClass:
        pass
    
    with pytest.warns(DeprecationWarning) as warning_info:
        result = _deprecated_alias(old_name, new_name, NewClass)
    
    # Assert that the result is the new_class
    assert result == NewClass
    
    # Check the warning message
    assert str(warning_info[0].message) == f"{old_name} is deprecated. Use {new_name}. This alias will be removed."

def test_deprecated_alias_empty_new_class(monkeypatch):
    # Mock the environment variable to simulate strict mode off
    monkeypatch.setenv("NOOGH_STRICT_MODE", "0")
    
    # Define old_name, new_name, and new_class for testing
    old_name = "old_function"
    new_name = "new_function"
    new_class = None
    
    with pytest.warns(DeprecationWarning) as warning_info:
        result = _deprecated_alias(old_name, new_name, new_class)
    
    # Assert that the result is None (assuming no meaningful output for invalid input)
    assert result is None
    
    # Check the warning message
    assert str(warning_info[0].message) == f"{old_name} is deprecated. Use {new_name}. This alias will be removed."

def test_deprecated_alias_invalid_new_class_type(monkeypatch):
    # Mock the environment variable to simulate strict mode off
    monkeypatch.setenv("NOOGH_STRICT_MODE", "0")
    
    # Define old_name, new_name, and new_class for testing
    old_name = "old_function"
    new_name = "new_function"
    new_class = 123
    
    with pytest.warns(DeprecationWarning) as warning_info:
        result = _deprecated_alias(old_name, new_name, new_class)
    
    # Assert that the result is None (assuming no meaningful output for invalid input)
    assert result == None
    
    # Check the warning message
    assert str(warning_info[0].message) == f"{old_name} is deprecated. Use {new_name}. This alias will be removed."