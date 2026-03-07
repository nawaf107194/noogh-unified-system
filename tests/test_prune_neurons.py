import pytest
from unittest.mock import patch

from noogh_unified_system.src.prune_neurons import auto_prune_if_needed, load_fabric, prune, logger

def test_auto_prune_if_needed_happy_path():
    with patch('noogh_unified_system.src.prune_neurons.load_fabric', return_value={"neurons": {}, "synapses": {}}):
        result = auto_prune_if_needed()
    assert result == {"skipped": True, "neurons": 0, "synapses": 0}

def test_auto_prune_if_needed_edge_case_empty_data():
    with patch('noogh_unified_system.src.prune_neurons.load_fabric', return_value={}):
        result = auto_prune_if_needed()
    assert result == {"skipped": True, "neurons": 0, "synapses": 0}

def test_auto_prune_if_needed_edge_case_boundary():
    with patch('noogh_unified_system.src.prune_neurons.load_fabric', return_value={"neurons": 3000, "synapses": 20000}):
        result = auto_prune_if_needed()
    assert result == {"skipped": True, "neurons": 3000, "synapses": 20000}

def test_auto_prune_if_needed_error_case_invalid_inputs():
    with patch('noogh_unified_system.src.prune_neurons.load_fabric', side_effect=Exception("Invalid input")):
        result = auto_prune_if_needed()
    assert result == {"error": "Invalid input"}

def test_auto_prune_if_needed_logs_info_on_pruning():
    with patch('noogh_unified_system.src.prune_neurons.load_fabric', return_value={"neurons": 3500, "synapses": 21000}):
        with patch.object(logger, 'info') as mock_info:
            auto_prune_if_needed()
        mock_info.assert_called_once_with("🧹 Auto-pruning: 3500 neurons, 21000 synapses (limits: 3000/20000)")