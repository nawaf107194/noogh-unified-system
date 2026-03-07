import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from noogh_wisdom import ActiveTrade, Decision

@pytest.fixture
def active_trade():
    decision = Decision(symbol="AAPL", direction="LONG", entry_price=150.0, leverage=1.0)
    trade = ActiveTrade(decision=decision, opened_at=time.time())
    return trade

@pytest.fixture
def mock_noogh_instance(active_trade):
    instance = MagicMock()
    instance.active_trades = [active_trade]
    instance.trade_history = []
    instance.stats = {"wins": 0, "losses": 0, "total_pnl": 0}
    instance._save = MagicMock()
    return instance

@pytest.mark.parametrize("direction, entry_price, close_price, expected_pnl", [
    ("LONG", 150.0, 160.0, 6.67),  # Long trade with profit
    ("SHORT", 150.0, 140.0, 6.67),  # Short trade with profit
    ("LONG", 150.0, 140.0, -6.67),  # Long trade with loss
    ("SHORT", 150.0, 160.0, -6.67),  # Short trade with loss
])
def test_close_trade_happy_path(mock_noogh_instance, direction, entry_price, close_price, expected_pnl):
    active_trade = mock_noogh_instance.active_trades[0]
    active_trade.decision.direction = direction
    active_trade.decision.entry_price = entry_price
    mock_noogh_instance._close_trade(active_trade, "Test Reason", close_price)
    
    assert active_trade.status == "Test Reason"
    assert active_trade.close_price == close_price
    assert active_trade.pnl_percent == pytest.approx(expected_pnl, abs=0.01)
    assert active_trade in mock_noogh_instance.trade_history
    assert active_trade not in mock_noogh_instance.active_trades
    assert mock_noogh_instance._save.called_once()

def test_close_trade_empty_active_trades(mock_noogh_instance):
    mock_noogh_instance.active_trades = []
    with pytest.raises(IndexError):
        mock_noogh_instance._close_trade(None, "Reason", 100.0)

def test_close_trade_none_trade(mock_noogh_instance):
    with pytest.raises(TypeError):
        mock_noogh_instance._close_trade(None, "Reason", 100.0)

def test_close_trade_invalid_reason(mock_noogh_instance, active_trade):
    with pytest.raises(TypeError):
        mock_noogh_instance._close_trade(active_trade, None, 100.0)

def test_close_trade_invalid_price(mock_noogh_instance, active_trade):
    with pytest.raises(TypeError):
        mock_noogh_instance._close_trade(active_trade, "Reason", "invalid_price")

def test_close_trade_async_behavior(mock_noogh_instance, active_trade):
    with patch('noogh_wisdom.time') as mock_time:
        mock_time.time.return_value = 1609459200  # Fixed timestamp for testing
        mock_noogh_instance._close_trade(active_trade, "Reason", 100.0)
        assert active_trade.closed_at == 1609459200