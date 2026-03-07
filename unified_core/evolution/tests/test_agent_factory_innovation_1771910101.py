import pytest
from unified_core.evolution.agent_factory import AgentFactory

@pytest.fixture
def agent_factory():
    return AgentFactory(registry_path='test_registry.json')

def test_save_registry_happy_path(agent_factory):
    # Setup: Create some agents with roles
    agent1 = {'role': 'roleA', 'data': 'data1'}
    agent2 = {'role': 'roleB', 'data': 'data2'}
    agent3 = {'role': 'roleA', 'data': 'data3'}  # Duplicate role, should overwrite
    
    agent_factory._generated_agents = [agent1, agent2, agent3]
    
    # Call the function
    agent_factory._save_registry()
    
    # Check: Registry file should contain two entries (no duplicates)
    with open('test_registry.json', 'r') as f:
        registry = json.load(f)
    
    assert len(registry) == 2
    assert 'roleA' in [agent['role'] for agent in registry]
    assert 'roleB' in [agent['role'] for agent in registry]

def test_save_registry_empty_list(agent_factory):
    # Setup: Empty list of agents
    agent_factory._generated_agents = []
    
    # Call the function
    agent_factory._save_registry()
    
    # Check: Registry file should be empty
    with open('test_registry.json', 'r') as f:
        registry = json.load(f)
    
    assert len(registry) == 0

def test_save_registry_none_input(agent_factory):
    # Setup: None input (should not raise an error and result in empty registry)
    agent_factory._generated_agents = None
    
    # Call the function
    agent_factory._save_registry()
    
    # Check: Registry file should be empty
    with open('test_registry.json', 'r') as f:
        registry = json.load(f)
    
    assert len(registry) == 0

def test_save_registry_invalid_input(agent_factory):
    # Setup: Invalid input (should not raise an error and result in empty registry)
    agent_factory._generated_agents = [None, {'role': None}, 'not a list']
    
    # Call the function
    agent_factory._save_registry()
    
    # Check: Registry file should be empty
    with open('test_registry.json', 'r') as f:
        registry = json.load(f)
    
    assert len(registry) == 0

def test_save_registry_async_behavior(agent_factory, event_loop):
    # Setup: Create some agents with roles
    agent1 = {'role': 'roleA', 'data': 'data1'}
    agent2 = {'role': 'roleB', 'data': 'data2'}
    
    agent_factory._generated_agents = [agent1, agent2]
    
    # Call the function asynchronously
    event_loop.run_until_complete(agent_factory.save_registry_async())
    
    # Check: Registry file should contain two entries (no duplicates)
    with open('test_registry.json', 'r') as f:
        registry = json.load(f)
    
    assert len(registry) == 2
    assert 'roleA' in [agent['role'] for agent in registry]
    assert 'roleB' in [agent['role'] for agent in registry]