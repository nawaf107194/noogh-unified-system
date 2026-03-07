import pytest
from src.unified_core.evolution.creative_agent import CreativeAgent

def test_set_world_model_valid():
    agent = CreativeAgent()
    test_model = {"test": "world_model"}
    agent.set_world_model(test_model)
    assert agent._world_model == test_model

def test_set_world_model_none():
    agent = CreativeAgent()
    agent.set_world_model(None)
    assert agent._world_model is None