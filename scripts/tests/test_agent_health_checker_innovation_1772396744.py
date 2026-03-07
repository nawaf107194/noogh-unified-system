import pytest
from your_module import AgentHealthChecker  # Replace with the actual import path

@pytest.fixture
def agent_health_checker():
    return AgentHealthChecker(registry_path="path/to/test/registry.json")

def test_happy_path(agent_health_checker):
    """Test normal inputs"""
    agent_health_checker.registry_path = "test_registry.json"
    with open("test_registry.json", 'w') as f:
        json.dump({"key": "value"}, f)
    
    result = agent_health_checker.load_registry()
    assert result == {"key": "value"}

def test_empty_file(agent_health_checker):
    """Test loading an empty file"""
    agent_health_checker.registry_path = "test_registry.json"
    with open("test_registry.json", 'w') as f:
        pass
    
    result = agent_health_checker.load_registry()
    assert result == {}

def test_non_existent_file(agent_health_checker):
    """Test loading a non-existent file"""
    agent_health_checker.registry_path = "non_existent_file.json"
    
    result = agent_health_checker.load_registry()
    assert result == []

def test_invalid_input_type(agent_health_checker):
    """Test with non-string input type for registry path"""
    agent_health_checker.registry_path = 123
    
    result = agent_health_checker.load_registry()
    assert result == []