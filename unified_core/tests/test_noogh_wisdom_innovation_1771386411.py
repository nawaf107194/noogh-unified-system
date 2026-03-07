import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Assuming ActiveTrade is defined elsewhere and DATA_DIR is a Path object
from noogh_wisdom import NooghWisdom, ActiveTrade
DATA_DIR = Path("/path/to/data")

class TestNooghWisdomInit:

    @pytest.fixture
    def noogh_instance(self):
        return NooghWisdom()

    def test_happy_path(self, noogh_instance):
        assert isinstance(noogh_instance.active_trades, list)
        assert isinstance(noogh_instance.trade_history, list)
        assert len(noogh_instance.active_trades) == 0
        assert len(noogh_instance.trade_history) == 0
        assert noogh_instance.stats == {"total": 0, "wins": 0, "losses": 0, "total_pnl": 0.0}
        assert DATA_DIR.exists()

    def test_edge_cases(self, noogh_instance):
        # Test if the lists remain empty after initialization
        assert not noogh_instance.active_trades
        assert not noogh_instance.trade_history

    def test_error_cases(self):
        with patch('noogh_wisdom.DATA_DIR.mkdir', side_effect=OSError):
            with pytest.raises(OSError):
                NooghWisdom()

    def test_async_behavior(self, noogh_instance):
        # Since the provided init method does not involve any async operations,
        # we can skip testing async behavior.
        pass

    @patch('noogh_wisdom.NooghWisdom._load')
    def test_load_called(self, mock_load, noogh_instance):
        mock_load.assert_called_once()