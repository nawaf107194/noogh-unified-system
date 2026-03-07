import pytest
from datetime import datetime, timedelta
import pandas as pd

from noogh_unified_system.src.agents.funding_scanner_v2 import FundingScannerV2

@pytest.fixture
def funding_scanner():
    return FundingScannerV2()

@pytest.fixture
def mock_rates():
    return [
        {
            "fundingTime": 1633072800000,
            "symbol": "BTCUSD",
            "fundingRate": "0.001"
        },
        {
            "fundingTime": 1633159200000,
            "symbol": "BTCUSD",
            "fundingRate": "-0.002"
        }
    ]

def test_get_funding_history_happy_path(funding_scanner, mock_rates):
    funding_scanner.client.futures_funding_rate = lambda *args, **kwargs: mock_rates
    df = funding_scanner.get_funding_history("BTCUSD")
    assert not df.empty
    assert 'fundingTime' in df.columns
    assert 'fundingRate' in df.columns

def test_get_funding_history_edge_case_empty(funding_scanner):
    funding_scanner.client.futures_funding_rate = lambda *args, **kwargs: []
    df = funding_scanner.get_funding_history("BTCUSD")
    assert df.empty

def test_get_funding_history_edge_case_boundary_days(funding_scanner, mock_rates):
    funding_scanner.client.futures_funding_rate = lambda *args, **kwargs: mock_rates
    df = funding_scanner.get_funding_history("BTCUSD", days=1)
    assert not df.empty
    assert len(df) == 2

def test_get_funding_history_error_case_invalid_symbol(funding_scanner):
    funding_scanner.client.futures_funding_rate = lambda *args, **kwargs: None
    df = funding_scanner.get_funding_history("INVALIDSYMBOL")
    assert df.empty