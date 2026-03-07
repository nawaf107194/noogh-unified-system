import pytest
from pathlib import Path
import json
from unittest.mock import patch, mock_open

from agents.paper_trading_with_neurons import PaperTradingWithNeurons

class MockResults:
    def __init__(self):
        self.results_file = Path('/home/noogh/projects/noogh_unified_system/src/data/neuron_test_results.json')
        self.neurons_dir = Path('/home/noogh/projects/noogh_unified_system/src/agents/neurons')

    @staticmethod
    def load_neuron(neuron_file):
        # Mock function to load a neuron
        with open(neuron_file, 'r') as f:
            return f.read()

def test_load_best_neurons_happy_path(monkeypatch, tmp_path):
    # Setup
    mock_results = MockResults()
    mock_results.neurons_dir.mkdir(parents=True)
    
    test_data = {
        "neuron1": {"improvement": 20, "passed": True},
        "neuron2": {"improvement": 15, "passed": True},
        "neuron3": {"improvement": 10, "passed": True}
    }
    
    mock_file = mock_open(read_data=json.dumps(test_data))
    monkeypatch.setattr("builtins.open", mock_file)
    monkeypatch.setattr(PaperTradingWithNeurons, "load_neuron", mock_results.load_neuron)

    agent = PaperTradingWithNeurons()
    agent.neurons_dir = mock_results.neurons_dir

    # Execute
    agent.load_best_neurons()

    # Assert
    assert len(agent.neurons) == 3
    assert agent.neurons[0]['name'] == 'neuron1'
    assert agent.neurons[0]['score'] == 20
    assert agent.neurons[1]['name'] == 'neuron2'
    assert agent.neurons[1]['score'] == 15
    assert agent.neurons[2]['name'] == 'neuron3'
    assert agent.neurons[2]['score'] == 10

def test_load_best_neurons_empty_results_file(monkeypatch):
    # Setup
    mock_results = MockResults()
    mock_results.results_file.touch()

    monkeypatch.setattr(PaperTradingWithNeurons, "load_neuron", lambda _: None)

    agent = PaperTradingWithNeurons()
    agent.neurons_dir = mock_results.neurons_dir

    # Execute
    agent.load_best_neurons()

    # Assert
    assert len(agent.neurons) == 0

def test_load_best_neurons_no_passed_neurons(monkeypatch):
    # Setup
    mock_results = MockResults()
    
    test_data = {
        "neuron1": {"improvement": 20, "passed": False},
        "neuron2": {"improvement": 15, "passed": False}
    }
    
    mock_file = mock_open(read_data=json.dumps(test_data))
    monkeypatch.setattr("builtins.open", mock_file)
    monkeypatch.setattr(PaperTradingWithNeurons, "load_neuron", lambda _: None)

    agent = PaperTradingWithNeurons()
    agent.neurons_dir = mock_results.neurons_dir

    # Execute
    agent.load_best_neurons()

    # Assert
    assert len(agent.neurons) == 0

def test_load_best_neurons_invalid_json(monkeypatch):
    # Setup
    mock_results = MockResults()
    
    test_data = "invalid json"
    
    mock_file = mock_open(read_data=test_data)
    monkeypatch.setattr("builtins.open", mock_file)

    agent = PaperTradingWithNeurons()
    agent.neurons_dir = mock_results.neurons_dir

    # Execute
    agent.load_best_neurons()

    # Assert
    assert len(agent.neurons) == 0

def test_load_best_neurons_missing_neuron_files(monkeypatch):
    # Setup
    mock_results = MockResults()
    
    test_data = {
        "neuron1": {"improvement": 20, "passed": True},
        "neuron2": {"improvement": 15, "passed": True}
    }
    
    mock_file = mock_open(read_data=json.dumps(test_data))
    monkeypatch.setattr("builtins.open", mock_file)
    monkeypatch.setattr(PaperTradingWithNeurons, "load_neuron", lambda _: None)

    agent = PaperTradingWithNeurons()
    agent.neurons_dir = mock_results.neurons_dir

    # Execute
    agent.load_best_neurons()

    # Assert
    assert len(agent.neurons) == 0