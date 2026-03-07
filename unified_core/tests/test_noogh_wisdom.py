import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from typing import List

# Assuming ActiveTrade is defined elsewhere and imported correctly.
# Also assuming DATA_DIR is defined as a Path object somewhere in the module.

class ActiveTrade:
    pass

DATA_DIR = Path("/path/to/data")

class NooGHWisdom:
    def __init__(self):
        self.active_trades: List[ActiveTrade] = []
        self.trade_history: List[ActiveTrade] = []
        self.stats = {"total": 0, "wins": 0, "losses": 0, "total_pnl": 0.0}
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        # Placeholder for actual implementation
        pass

@pytest.fixture
def nooghwisdom_instance():
    return NooGHWisdom()

def test_init_happy_path(nooghwisdom_instance):
    assert isinstance(nooghwisdom_instance.active_trades, list)
    assert isinstance(nooghwisdom_instance.trade_history, list)
    assert isinstance(nooghwisdom_instance.stats, dict)
    assert len(nooghwisdom_instance.active_trades) == 0
    assert len(nooghwisdom_instance.trade_history) == 0
    assert nooghwisdom_instance.stats == {"total": 0, "wins": 0, "losses": 0, "total_pnl": 0.0}

def test_init_data_dir_creation(mocker):
    mocker.patch('pathlib.Path.mkdir')
    instance = NooGHWisdom()
    DATA_DIR.mkdir.assert_called_once_with(parents=True, exist_ok=True)

def test_init_load_called(mocker):
    mock_load = mocker.patch.object(NooGHWisdom, '_load')
    instance = NooGHWisdom()
    mock_load.assert_called_once()

def test_init_edge_cases():
    instance = NooGHWisdom()
    assert instance.active_trades == []
    assert instance.trade_history == []

def test_init_error_cases(mocker):
    mocker.patch('pathlib.Path.mkdir', side_effect=OSError("Mocked error"))
    with pytest.raises(OSError):
        NooGHWisdom()