import pytest

from unified_core.evolution.creative_agent import CreativeAgent

def test_happy_path():
    agent = CreativeAgent(name="TestAgent", weight=0.5)
    assert agent.name == "TestAgent"
    assert agent.weight == 0.5
    assert agent._last_run == 0.0
    assert agent._cooldown == 300.0
    assert agent._run_count == 0
    assert agent._success_count == 0

def test_empty_name():
    agent = CreativeAgent(name="")
    assert agent.name == ""
    assert agent.weight == 1.0
    assert agent._last_run == 0.0
    assert agent._cooldown == 300.0
    assert agent._run_count == 0
    assert agent._success_count == 0

def test_none_name():
    agent = CreativeAgent(name=None)
    assert agent.name is None
    assert agent.weight == 1.0
    assert agent._last_run == 0.0
    assert agent._cooldown == 300.0
    assert agent._run_count == 0
    assert agent._success_count == 0

def test_boundary_weight():
    agent = CreativeAgent(name="TestAgent", weight=1.0)
    assert agent.name == "TestAgent"
    assert agent.weight == 1.0
    assert agent._last_run == 0.0
    assert agent._cooldown == 300.0
    assert agent._run_count == 0
    assert agent._success_count == 0

def test_negative_weight():
    with pytest.raises(ValueError):
        CreativeAgent(name="TestAgent", weight=-1.0)

def test_large_weight():
    with pytest.raises(ValueError):
        CreativeAgent(name="TestAgent", weight=2.0)