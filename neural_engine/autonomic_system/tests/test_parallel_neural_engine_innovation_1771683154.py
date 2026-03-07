import pytest

from neural_engine.autonomic_system.parallel_neural_engine import NeuralEngine, Neuron

class MockNeuron(Neuron):
    def __init__(self, layer: int, processing: bool):
        self.layer = layer
        self.processing = processing

@pytest.fixture
def empty_neural_engine():
    return NeuralEngine()

@pytest.fixture
def simple_neural_engine():
    neurons = [
        MockNeuron(0, True),
        MockNeuron(0, False),
        MockNeuron(1, True),
        MockNeuron(1, True)
    ]
    engine = NeuralEngine()
    for neuron in neurons:
        engine.neurons.append(neuron)
    return engine

def test_happy_path(simple_neural_engine):
    result = simple_neural_engine.visualize_neural_activity()
    expected_output = """
🧠 Neural Activity Visualization:

Layer 0: [█░] 1/2 active
Layer 1: [██] 2/2 active
"""
    assert result == expected_output

def test_edge_case_empty(empty_neural_engine):
    result = empty_neural_engine.visualize_neural_activity()
    expected_output = """
🧠 Neural Activity Visualization:

"""
    assert result == expected_output

def test_edge_case_none():
    with pytest.raises(AttributeError):
        None.visualize_neural_activity()

def test_error_cases_invalid_input_with_exception():
    class InvalidNeuron:
        pass

    engine = NeuralEngine()
    engine.neurons.append(InvalidNeuron())
    
    with pytest.raises(AssertionError):
        result = engine.visualize_neural_activity()