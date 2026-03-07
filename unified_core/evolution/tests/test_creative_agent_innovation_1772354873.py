import pytest

from unified_core.evolution.creative_agent import CreativeAgent

class MockSuperClass:
    def __init__(self, name, weight):
        self.name = name
        self.weight = weight

def test_creative_agent_init_happy_path():
    agent = CreativeAgent()
    assert agent.name == "curiosity"
    assert agent.weight == 0.5
    assert agent._cooldown == 1800.0

def test_creative_agent_init_default_cooldown():
    agent = CreativeAgent()
    assert agent._cooldown == 1800.0

def test_creative_agent_init_custom_weight():
    agent = CreativeAgent(weight=0.75)
    assert agent.weight == 0.75