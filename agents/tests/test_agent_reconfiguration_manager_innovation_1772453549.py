import pytest
from agents.agent_reconfiguration_manager import AgentReconfigurationManager

class MockAgent:
    def __init__(self):
        self.config = {}

    def update_config(self, new_config):
        self.config.update(new_config)

@pytest.fixture
def reconfig_manager():
    return AgentReconfigurationManager()

def test_update_agent_config_happy_path(reconfig_manager):
    agent_name = "agent1"
    new_config = {"key": "value"}
    
    mock_agent = MockAgent()
    reconfig_manager.agents[agent_name] = mock_agent
    
    reconfig_manager.update_agent_config(agent_name, new_config)
    
    assert mock_agent.config == new_config

def test_update_agent_config_empty_config(reconfig_manager):
    agent_name = "agent1"
    new_config = {}
    
    mock_agent = MockAgent()
    reconfig_manager.agents[agent_name] = mock_agent
    
    reconfig_manager.update_agent_config(agent_name, new_config)
    
    assert mock_agent.config == {}

def test_update_agent_config_none_config(reconfig_manager):
    agent_name = "agent1"
    new_config = None
    
    mock_agent = MockAgent()
    reconfig_manager.agents[agent_name] = mock_agent
    
    with pytest.raises(KeyError) as exc_info:
        reconfig_manager.update_agent_config(agent_name, new_config)
    
    assert str(exc_info.value) == f"Agent {agent_name} not found."

def test_update_agent_config_non_existent_agent(reconfig_manager):
    agent_name = "non_existent"
    new_config = {"key": "value"}
    
    with pytest.raises(KeyError) as exc_info:
        reconfig_manager.update_agent_config(agent_name, new_config)
    
    assert str(exc_info.value) == f"Agent {agent_name} not found."