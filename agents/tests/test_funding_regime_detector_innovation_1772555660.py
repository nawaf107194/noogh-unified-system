import pytest
from pandas import DataFrame
from unittest.mock import patch
from datetime import datetime, timedelta
from src.agents.funding_regime_detector import FundingRegimeDetector

@pytest.fixture
def funding_detector():
    return FundingRegimeDetector()

@pytest.fixture
def mock_client():
    with patch('src.agents.funding_regime_detector.Client') as mock:
        yield mock

@pytest.fixture
def mock_rates():
    return [
        {'fundingTime': int((datetime.now() - timedelta(days=1)).timestamp() * 1000), 'fundingRate': '0.0001'},
        {'fundingTime': int((datetime.now() - timedelta(days=2)).timestamp() * 1000), 'fundingRate': '0.0002'}
    ]

def test_get_funding_history_happy_path(funding_detector, mock_client, mock_rates):
    mock_instance = mock_client.return_value
    mock_instance.futures_funding_rate.return_value = mock_rates

    result = funding_detector.get_funding_history('BTCUSDT')
    
    assert isinstance(result, DataFrame)
    assert not result.empty
    assert list(result.columns) == ['fundingRate']
    assert isinstance(result.index, pd.DatetimeIndex)

def test_get_funding_history_empty_response(funding_detector, mock_client):
    mock_instance = mock_client.return_value
    mock_instance.futures_funding_rate.return_value = []

    result = funding_detector.get_funding_history('BTCUSDT')
    assert isinstance(result, DataFrame)
    assert result.empty

def test_get_funding_history_zero_days(funding_detector, mock_client, mock_rates):
    mock_instance = mock_client.return_value
    mock_instance.futures_funding_rate.return_value = mock_rates

    result = funding_detector.get_funding_history('BTCUSDT', days=0)
    
    assert isinstance(result, DataFrame)
    assert not result.empty

def test_get_funding_history_invalid_symbol(funding_detector):
    result = funding_detector.get_funding_history(123)  # Invalid symbol type
    assert isinstance(result, DataFrame)
    assert result.empty

def test_get_funding_history_negative_days(funding_detector):
    result = funding_detector.get_funding_history('BTCUSDT', days=-1)
    assert isinstance(result, DataFrame)
    assert result.empty