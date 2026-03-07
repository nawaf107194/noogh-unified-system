import pytest
from pathlib import Path
import json
from unittest.mock import patch, MagicMock

def mock_get_neuron_fabric():
    fabric = MagicMock()
    fabric._neurons = {
        "NEURON-1": MagicMock(metadata={"proposal_id": "EVO-TEST"}),
        "NEURON-2": MagicMock(),
        "NEURON-3": MagicMock(proposition="B-Tree")
    }
    return fabric

def test_repair_system_happy_path():
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open") as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.read.return_value = json.dumps({
                "fragile_paths": {
                    "src/test_target/path1": "value",
                    "src/imaginary_test/path2": "value"
                }
            })
            with patch("json.dump") as mock_json_dump:
                with patch("unified_core.evolution.ledger.EvolutionLedger.exit_safe_mode"):
                    repair_system()
                    
                assert mock_file.read.call_count == 1
                assert mock_json_dump.call_args[0][0]['fragile_paths'] == {}
                mock_json_dump.assert_called_once()
                assert "Repair complete!" in capsys.readouterr().out

def test_repair_system_empty_memory():
    with patch("pathlib.Path.exists", return_value=False):
        repair_system()
        assert "EvolutionMemory Fragile list is already clean." in capsys.readouterr().out

def test_repair_system_empty_ledger():
    with patch("pathlib.Path.exists", side_effect=[True, False]):
        with patch("builtins.open") as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.read.return_value = json.dumps({
                "fragile_paths": {
                    "src/test_target/path1": "value",
                    "src/imaginary_test/path2": "value"
                }
            })
        repair_system()
        assert "Ledger is already out of safe mode." in capsys.readouterr().out

def test_repair_system_error_during_memory_cleaning():
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open") as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.read.side_effect = Exception("Test error")
        repair_system()
        assert "Failed to clean memory" in capsys.readouterr().err

def test_repair_system_error_during_ledger_reset():
    with patch("pathlib.Path.exists", side_effect=[True, True]):
        with patch("builtins.open") as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.read.return_value = json.dumps({
                "fragile_paths": {
                    "src/test_target/path1": "value",
                    "src/imaginary_test/path2": "value"
                }
            })
        with patch("unified_core.evolution.ledger.EvolutionLedger.exit_safe_mode") as mock_exit_safe_mode:
            mock_exit_safe_mode.side_effect = Exception("Test error")
        repair_system()
        assert "Failed to exit safe mode" in capsys.readouterr().err

def test_repair_system_error_during_neuron_healing():
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open") as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.read.return_value = json.dumps({
                "fragile_paths": {
                    "src/test_target/path1": "value",
                    "src/imaginary_test/path2": "value"
                }
            })
        with patch("unified_core.evolution.neuron_learning.get_neuron_learning_bridge") as mock_get_neuron_learning_bridge:
            mock_get_neuron_learning_bridge.return_value = MagicMock()
        with patch("unified_core.core.neuron_fabric.get_neuron_fabric", side_effect=Exception("Test error")):
            repair_system()
        assert "Could not repair Neurons" in capsys.readouterr().err