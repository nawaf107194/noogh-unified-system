import pytest
import os
import json
from unittest.mock import patch, mock_open
from .neuron_fabric import NeuronFabric, NeuronType, Neuron, Synapse, NeuronCluster

@pytest.fixture
def neuron_fabric():
    return NeuronFabric("test_path.json")

@patch('builtins.open', new_callable=mock_open)
def test_load_happy_path(mock_file, neuron_fabric):
    mock_data = {
        "neurons": {
            "1": {"neuron_id": 1, "proposition": "p1", "energy": 0.8},
            "2": {"neuron_id": 2, "proposition": "p2"}
        },
        "synapses": {
            "3": {"source_id": 1, "target_id": 2}
        }
    }
    mock_file.return_value.__iter__.return_value = json.dumps(mock_data).splitlines()
    
    neuron_fabric._load()
    
    assert len(neuron_fabric._neurons) == 2
    assert len(neuron_fabric._synapses) == 1
    
    neuron1 = neuron_fabric._neurons["1"]
    neuron2 = neuron_fabric._neurons["2"]
    synapse1 = neuron_fabric._synapses["3"]
    
    assert neuron1.neuron_id == 1
    assert neuron1.proposition == "p1"
    assert neuron2.neuron_id == 2
    assert neuron2.proposition == "p2"
    assert synapse1.source_id == 1
    assert synapse1.target_id == 2

def test_load_empty_file(neuron_fabric):
    with patch('builtins.open', new_callable=mock_open, read_data=""):
        neuron_fabric._load()
    
    assert not neuron_fabric._neurons
    assert not neuron_fabric._synapses

@patch('builtins.open', side_effect=FileNotFoundError)
def test_load_file_not_found(mock_file, neuron_fabric):
    neuron_fabric._load()
    
    assert not neuron_fabric._neurons
    assert not neuron_fabric._synapses

def test_load_invalid_json(neuron_fabric):
    with patch('builtins.open', new_callable=mock_open, read_data="invalid json"):
        neuron_fabric._load()
    
    assert not neuron_fabric._neurons
    assert not neuron_fabric._synapses