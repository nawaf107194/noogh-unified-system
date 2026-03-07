import pytest
from datetime import datetime, timedelta
import pandas as pd
from unittest.mock import patch

from agents.funding_regime_detector import FundingRegimeDetector

def mock_futures_funding_rate(symbol, startTime, endTime, limit):
    if symbol == "invalid_symbol":
        return None
    elif symbol == "empty_rates":
        return []
    else:
        return [
            {
                'fundingTime': int((datetime.now() - timedelta(days=1)).timestamp() * 1000),
                'fundingRate': '0.001'
            },
            {
                'fundingTime': int(datetime.now().timestamp() * 1000),
                'fundingRate': '-0.002'
            }
        ]

@patch('agents.funding_regime_detector.FundingRegimeDetector.client.futures_funding_rate', side_effect=mock_futures_funding_rate)
def test_get_funding_history_happy_path(mock_client):
    detector = FundingRegimeDetector()
    result = detector.get_funding_history("BTCUSDT")
    
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert '2023-04-17' in result.index
    assert '2023-04-18' in result.index
    assert result.loc['2023-04-17', 'fundingRate'] == 0.001
    assert result.loc['2023-04-18', 'fundingRate'] == -0.002

@patch('agents.funding_regime_detector.FundingRegimeDetector.client.futures_funding_rate')
def test_get_funding_history_empty_rates(mock_client):
    mock_client.return_value = []
    detector = FundingRegimeDetector()
    result = detector.get_funding_history("empty_rates")
    
    assert isinstance(result, pd.DataFrame)
    assert result.empty

@patch('agents.funding_regime_detector.FundingRegimeDetector.client.futures_funding_rate')
def test_get_funding_history_invalid_symbol(mock_client):
    mock_client.return_value = None
    detector = FundingRegimeDetector()
    result = detector.get_funding_history("invalid_symbol")
    
    assert isinstance(result, pd.DataFrame)
    assert result.empty

@patch('agents.funding_regime_detector.FundingRegimeDetector.client.futures_funding_rate')
def test_get_funding_history_none_symbol(mock_client):
    detector = FundingRegimeDetector()
    with pytest.raises(TypeError) as exc_info:
        detector.get_funding_history(None)
    
    assert str(exc_info.value) == "symbol must be a non-empty string"

@patch('agents.funding_regime_detector.FundingRegimeDetector.client.futures_funding_rate')
def test_get_funding_history_non_int_days(mock_client):
    detector = FundingRegimeDetector()
    with pytest.raises(TypeError) as exc_info:
        detector.get_funding_history("BTCUSDT", "7")
    
    assert str(exc_info.value) == "days must be an integer"