import pytest
from unittest.mock import MagicMock
from pathlib import Path
import time

from unified_core.evolution.agent_factory import AgentFactory, AgentBlueprint, AgentRole

class TestAgentFactory:

    @pytest.fixture
    def agent_factory(self):
        factory = AgentFactory()
        factory.agents_dir = Path("/tmp/test_agents")
        factory.BUILTIN_BLUEPRINTS = {
            "health_monitor": MagicMock(AgentBlueprint)
        }
        factory._generate_code = MagicMock(return_value="class TestAgent: pass")
        factory._validate_agent_code = MagicMock(return_value={"valid": True, "violations": []})
        factory._register_role = MagicMock()
        factory._generated_agents = []
        factory._save_registry = MagicMock()
        return factory

    def test_happy_path(self, agent_factory):
        result = agent_factory.generate_agent(blueprint_id="health_monitor")
        assert result == {
            "success": True,
            "agent_file": str(agent_factory.agents_dir / "health_monitor_agent.py"),
            "class_name": "TestAgent",
            "role": None,
            "capabilities": [],
            "validation": {"valid": True, "violations": []}
        }
        
        agent_factory._generate_code.assert_called_once_with(agent_factory.BUILTIN_BLUEPRINTS["health_monitor"])
        agent_factory._validate_agent_code.assert_called_once_with("class TestAgent: pass", agent_factory.BUILTIN_BLUEPRINTS["health_monitor"])
        assert not agent_factory.agents_dir / "health_monitor_agent.py".exists()
        agent_factory._register_role.assert_called_once_with(None)
        assert len(agent_factory._generated_agents) == 1
        agent_factory._save_registry.assert_called_once()

    def test_empty_blueprint_id(self, agent_factory):
        result = agent_factory.generate_agent(blueprint_id="")
        assert result == {
            "success": False,
            "error": "Unknown blueprint: "
        }
        
        agent_factory._generate_code.assert_not_called()
        agent_factory._validate_agent_code.assert_not_called()
        assert not agent_factory.agents_dir / "health_monitor_agent.py".exists()
        agent_factory._register_role.assert_not_called()
        assert len(agent_factory._generated_agents) == 0
        agent_factory._save_registry.assert_not_called()

    def test_none_blueprint(self, agent_factory):
        result = agent_factory.generate_agent(blueprint=None)
        assert result == {
            "success": False,
            "error": "Unknown blueprint: None"
        }
        
        agent_factory._generate_code.assert_not_called()
        agent_factory._validate_agent_code.assert_not_called()
        assert not agent_factory.agents_dir / "health_monitor_agent.py".exists()
        agent_factory._register_role.assert_not_called()
        assert len(agent_factory._generated_agents) == 0
        agent_factory._save_registry.assert_not_called()

    def test_existing_agent_file(self, agent_factory):
        (agent_factory.agents_dir / "health_monitor_agent.py").touch(exist_ok=True)
        result = agent_factory.generate_agent(blueprint_id="health_monitor")
        assert result == {
            "success": False,
            "error": "Agent already exists: /tmp/test_agents/health_monitor_agent.py",
            "hint": "Delete the file first or use a different role"
        }
        
        agent_factory._generate_code.assert_not_called()
        agent_factory._validate_agent_code.assert_not_called()
        assert not agent_factory.agents_dir / "health_monitor_agent.py".exists()
        agent_factory._register_role.assert_not_called()
        assert len(agent_factory._generated_agents) == 0
        agent_factory._save_registry.assert_not_called()

    def test_validation_failure(self, agent_factory):
        agent_factory._validate_agent_code.return_value = {"valid": False, "violations": ["Error"]}
        result = agent_factory.generate_agent(blueprint_id="health_monitor")
        assert result == {
            "success": False,
            "error": "Validation failed",
            "violations": ["Error"]
        }
        
        agent_factory._generate_code.assert_called_once_with(agent_factory.BUILTIN_BLUEPRINTS["health_monitor"])
        agent_factory._validate_agent_code.assert_called_once_with("class TestAgent: pass", agent_factory.BUILTIN_BLUEPRINTS["health_monitor"])
        assert not agent_factory.agents_dir / "health_monitor_agent.py".exists()
        agent_factory._register_role.assert_not_called()
        assert len(agent_factory._generated_agents) == 0
        agent_factory._save_registry.assert_not_called()

    def test_async_behavior(self, agent_factory):
        with pytest.raises(NotImplementedError):
            result = agent_factory.generate_agent(blueprint_id="health_monitor", async_mode=True)

# Run tests
if __name__ == "__main__":
    pytest.main()