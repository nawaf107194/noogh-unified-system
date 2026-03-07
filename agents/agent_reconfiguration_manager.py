import json
from typing import Dict, Any

class AgentReconfigurationManager:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.agents = {}

    def load_config(self, path: str) -> Dict[str, Any]:
        with open(path, 'r') as file:
            return json.load(file)

    def register_agent(self, agent_name: str, agent_instance):
        self.agents[agent_name] = agent_instance

    def update_agent_config(self, agent_name: str, new_config: Dict[str, Any]):
        if agent_name in self.agents:
            self.agents[agent_name].update_config(new_config)
        else:
            raise KeyError(f"Agent {agent_name} not found.")

    def reconfigure_agents(self):
        for agent_name, agent in self.agents.items():
            agent.reconfigure(self.config.get(agent_name, {}))

# Example usage
if __name__ == "__main__":
    # Assume we have a configuration file with agent settings
    config_path = 'config/agent_configs.json'
    
    # Create an instance of the reconfiguration manager
    manager = AgentReconfigurationManager(config_path)
    
    # Register some agents (this part depends on your actual agent implementation)
    # manager.register_agent('example_agent', ExampleAgent())
    
    # Reconfigure all registered agents
    manager.reconfigure_agents()