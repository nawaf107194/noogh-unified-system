import pytest
from noogh_unified_system.src.unified_core.evolution.agent_factory import AgentFactory

# Mocking Pathlib.Path to simulate different scenarios
class MockPath:
    def __init__(self, exists_value):
        self.exists_value = exists_value
        self.is_file = True

    def exists(self):
        return self.exists_value

    @property
    def is_file(self):
        return self.is_file

# Test cases
def test_load_registry_happy_path(mocker):
    factory = AgentFactory()
    mock_path = MockPath(True)
    mock_path.open = mocker.mock_open(read_data='{"agent1": "data1", "agent2": "data2"}')
    
    with mocker.patch.object(factory, '_registry_path', new=mock_path):
        factory._load_registry()
    
    assert factory._generated_agents == {"agent1": "data1", "agent2": "data2"}

def test_load_registry_empty_file(mocker):
    factory = AgentFactory()
    mock_path = MockPath(True)
    mock_path.open = mocker.mock_open(read_data='{}')
    
    with mocker.patch.object(factory, '_registry_path', new=mock_path):
        factory._load_registry()
    
    assert factory._generated_agents == {}

def test_load_registry_nonexistent_file(mocker):
    factory = AgentFactory()
    mock_path = MockPath(False)
    
    with mocker.patch.object(factory, '_registry_path', new=mock_path):
        factory._load_registry()
    
    assert factory._generated_agents == []

def test_load_registry_invalid_json(mocker):
    factory = AgentFactory()
    mock_path = MockPath(True)
    mock_path.open = mocker.mock_open(read_data='invalid json')
    
    with pytest.raises(json.JSONDecodeError) as exc_info:
        with mocker.patch.object(factory, '_registry_path', new=mock_path):
            factory._load_registry()
    
    assert(exc_info.type is json.JSONDecodeError)

def test_load_registry_non_file(mocker):
    factory = AgentFactory()
    mock_path = MockPath(True)
    mock_path.is_file = False
    
    with mocker.patch.object(factory, '_registry_path', new=mock_path):
        factory._load_registry()
    
    assert factory._generated_agents == []