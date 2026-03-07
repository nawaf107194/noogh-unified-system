import pytest

from unified_core.core.neuron_pulse import NeuronPulse

class MockFabric:
    def __init__(self):
        self.activated = None
    
    def activate_by_query(self, query, top_k):
        if not query or "signal market" in query:
            return []
        else:
            return ["neuron1", "neuron2"]
    
    def learn_from_outcome(self, activated, success, impact):
        self.activated = activated

@pytest.fixture
def neuron_pulse():
    return NeuronPulse(fabric=MockFabric())

def test_learn_from_trade_happy_path(neuron_pulse):
    symbol = "AAPL"
    direction = "buy"
    success = True
    confidence = 0.75
    
    neuron_pulse.learn_from_trade(symbol, direction, success, confidence)
    
    assert neuron_pulse._total_learnings == 1
    assert neuron_pulse.fabric.activated == ["neuron1", "neuron2"]

def test_learn_from_trade_edge_case_empty_symbol(neuron_pulse):
    neuron_pulse.learn_from_trade("", "buy", True)
    assert neuron_pulse._total_learnings == 0
    assert neuron_pulse.fabric.activated is None

def test_learn_from_trade_edge_case_none_direction(neuron_pulse):
    neuron_pulse.learn_from_trade("AAPL", None, False)
    assert neuron_pulse._total_learnings == 0
    assert neuron_pulse.fabric.activated is None

def test_learn_from_trade_edge_case_boundary_confidence(neuron_pulse):
    neuron_pulse.learn_from_trade("AAPL", "buy", True, 0.99)
    assert neuron_pulse._total_learnings == 1
    assert neuron_pulse.fabric.activated == ["neuron1", "neuron2"]

def test_learn_from_trade_error_case_invalid_symbol(neuron_pulse):
    neuron_pulse.learn_from_trade("invalid@symbol", "buy", True)
    assert neuron_pulse._total_learnings == 0
    assert neuron_pulse.fabric.activated == []

# Assuming no async behavior in this function, so no need for specific async tests