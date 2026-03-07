import pytest

from unified_core.core.config_manager import ConfigManager

def test_happy_path():
    instance1 = ConfigManager()
    instance2 = ConfigManager()
    
    assert instance1 is instance2
    assert isinstance(instance1, ConfigManager)
    assert isinstance(instance2, ConfigManager)

def test_first_instance_creation():
    instance = ConfigManager()
    assert isinstance(instance.config, dict)
    assert instance._instance is not None

def test_subsequent_instances_same_as_first():
    instance1 = ConfigManager()
    instance2 = ConfigManager()
    
    assert instance1 == instance2
    assert instance1 is instance2
    
def test_config_attribute_exists():
    instance = ConfigManager()
    assert hasattr(instance, 'config')
    assert isinstance(instance.config, dict)

def test_no_new_instances_on_subsequent_calls():
    instance1 = ConfigManager()
    instance2 = ConfigManager()
    
    assert instance1._instance is not None
    assert instance1._instance is instance2._instance

# Testing edge cases (empty, None, boundaries) for completeness
# However, since __new__ does not accept any parameters and always returns the same instance,
# there are no meaningful edge cases to test.