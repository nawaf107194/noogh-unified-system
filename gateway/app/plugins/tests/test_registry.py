import pytest

from gateway.app.plugins.registry import Registry

def test_clear_happy_path():
    registry = Registry()
    registry.plugins['plugin1'] = 'some_plugin'
    registry.tools['tool1'] = 'some_tool'
    
    registry.clear()
    
    assert not registry.plugins, "Plugins should be cleared"
    assert not registry.tools, "Tools should be cleared"

def test_clear_empty():
    registry = Registry()
    
    registry.clear()
    
    assert not registry.plugins, "Plugins should be empty"
    assert not registry.tools, "Tools should be empty"

def test_clear_none():
    registry = None
    
    with pytest.raises(AttributeError) as e:
        registry.clear()
    
    assert str(e.value) == "'NoneType' object has no attribute 'clear'", "Should raise AttributeError when called on None"

# Async behavior is not applicable for this function, so no additional tests are needed