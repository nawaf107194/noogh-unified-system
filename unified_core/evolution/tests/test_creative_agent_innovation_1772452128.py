import pytest

from unified_core.evolution.creative_agent import CreativeAgent

def test_set_world_model_happy_path():
    agent = CreativeAgent()
    wm = "Test World Model"
    agent.set_world_model(wm)
    assert agent._world_model == wm, "World model should be set correctly"

def test_set_world_model_none():
    agent = CreativeAgent()
    agent.set_world_model(None)
    assert agent._world_model is None, "World model should be set to None"

def test_set_world_model_empty_string():
    agent = CreativeAgent()
    agent.set_world_model("")
    assert agent._world_model == "", "World model should be set to empty string"

def test_set_world_model_boundary_case():
    agent = CreativeAgent()
    wm = "a" * 1024  # Assuming boundary is around 1024 characters
    agent.set_world_model(wm)
    assert agent._world_model == wm, "World model should be set correctly even for large strings"

def test_set_world_model_invalid_input():
    agent = CreativeAgent()
    with pytest.raises(TypeError) as exc_info:
        agent.set_world_model(12345)
    assert str(exc_info.value) == "Invalid input type: int", "Should raise TypeError for invalid input types"