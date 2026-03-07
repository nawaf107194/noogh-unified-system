import pytest
from unified_core.core.neuron_pulse import NeuronPulse

def test_get_stats_happy_path():
    pulse = NeuronPulse()
    pulse._total_activations = 10
    pulse._total_learnings = 5
    pulse._domain_stats = {"example": 2}
    
    result = pulse.get_stats()
    
    assert result == {
        "total_activations": 10,
        "total_learnings": 5,
        "domain_stats": {"example": 2},
    }

def test_get_stats_empty_stats():
    pulse = NeuronPulse()
    pulse._total_activations = 0
    pulse._total_learnings = 0
    pulse._domain_stats = {}
    
    result = pulse.get_stats()
    
    assert result == {
        "total_activations": 0,
        "total_learnings": 0,
        "domain_stats": {},
    }

def test_get_stats_none_values():
    pulse = NeuronPulse()
    pulse._total_activations = None
    pulse._total_learnings = None
    pulse._domain_stats = None
    
    result = pulse.get_stats()
    
    assert result == {
        "total_activations": None,
        "total_learnings": None,
        "domain_stats": None,
    }

def test_get_stats_invalid_input():
    pulse = NeuronPulse()
    
    with pytest.raises(TypeError):
        pulse._total_activations = "not_an_int"
        pulse.get_stats()
    
    with pytest.raises(TypeError):
        pulse._total_learnings = "not_an_int"
        pulse.get_stats()
    
    with pytest.raises(ValueError):
        pulse._domain_stats = {"example": "not_a_number"}
        pulse.get_stats()

def test_get_stats_async_behavior():
    # Assuming get_stats is synchronous, there's no need for async testing here.
    pass