import pytest

from unified_core.evolution.evolution_triggers import EvolutionTriggers

def test_set_world_model_happy_path():
    triggers = EvolutionTriggers()
    wm = {}
    triggers.set_world_model(wm)
    assert triggers._world_model == wm

def test_set_world_model_none():
    triggers = EvolutionTriggers()
    triggers.set_world_model(None)
    assert triggers._world_model is None

def test_set_world_model_empty_dict():
    triggers = EvolutionTriggers()
    wm = {}
    triggers.set_world_model(wm)
    assert triggers._world_model == wm

def test_set_world_model_invalid_input_type():
    triggers = EvolutionTriggers()
    with pytest.raises(TypeError):
        triggers.set_world_model("not a dictionary")