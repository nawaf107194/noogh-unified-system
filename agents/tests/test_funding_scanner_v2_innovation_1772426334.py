from datetime import datetime, timedelta
import pandas as pd
from unittest.mock import patch
from noogh_unified_system.src.agents.funding_scanner_v2 import FundingScanner

def mock_client_funding_rate(*args, **kwargs):
    return [
        {
            "fundingRate": "0.001",
            "fundingTime": "1633072800000"
        },
        {
            "fundingRate": "-0.002",
            "fundingTime": "1633159200000"
        }
    ]

@pytest.fixture
def funding_scanner():
    return FundingScanner()

@patch.object(FundingScanner, 'client', create=True)
def test_get_funding_history_happy_path(funding_scanner):
    with patch.object(funding_scanner.client, 'futures_funding_rate', side_effect=mock_client_funding_rate):
        result = funding_scanner.get_funding_history(symbol="BTCUSDT")
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert '2021-09-30 00:00:00' in result.index
        assert '2021-10-01 00:00:00' in result.index

@patch.object(FundingScanner, 'client', create=True)
def test_get_funding_history_empty(funding_scanner):
    with patch.object(funding_scanner.client, 'futures_funding_rate', return_value=[]):
        result = funding_scanner.get_funding_history(symbol="BTCUSDT")
        assert isinstance(result, pd.DataFrame)
        assert result.empty

@patch.object(FundingScanner, 'client', create=True)
def test_get_funding_history_invalid_symbol(funding_scanner):
    with patch.object(funding_scanner.client, 'futures_funding_rate', side_effect=Exception("Invalid symbol")):
        result = funding_scanner.get_funding_history(symbol="INVALID")
        assert isinstance(result, pd.DataFrame)
        assert result.empty

@patch.object(FundingScanner, 'client', create=True)
def test_get_funding_history_no_client(funding_scanner):
    with patch.object(funding_scanner.client, '__init__', side_effect=AttributeError("Client attribute not found")):
        result = funding_scanner.get_funding_history(symbol="BTCUSDT")
        assert isinstance(result, pd.DataFrame)
        assert result.empty