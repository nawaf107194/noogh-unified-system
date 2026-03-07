import pytest
from datetime import datetime, timedelta
import pandas as pd

# Assuming FundingRegimeDetector is already defined and available for testing
from your_module_path.funding_regime_detector import FundingRegimeDetector  # Replace with actual module path

@pytest.fixture
def client(mocker):
    mock_client = mocker.Mock()
    mock_client.futures_funding_rate.return_value = [
        {
            'fundingTime': int((datetime.now() - timedelta(days=1)).timestamp() * 1000),
            'symbol': 'BTCUSD',
            'fundingRate': '0.0002'
        }
    ]
    return mock_client

@pytest.fixture
def detector(client):
    return FundingRegimeDetector(client)

def test_happy_path(detector):
    result = detector.get_funding_history('BTCUSD')
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert 'fundingTime' in result.columns
    assert 'fundingRate' in result.columns

def test_edge_case_empty_result(client, detector):
    client.futures_funding_rate.return_value = []
    result = detector.get_funding_history('BTCUSD')
    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert not result.columns.has_categories

def test_edge_case_invalid_symbol(detector):
    result = detector.get_funding_history(None)
    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert not result.columns.has_categories

def test_error_case_negative_days(detector):
    result = detector.get_funding_history('BTCUSD', days=-1)
    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert not result.columns.has_categories

def test_async_behavior(mocker, client, detector):
    mock_client = mocker.patch.object(FundingRegimeDetector, 'client', new=client)
    mock_client.futures_funding_rate.return_value = [
        {
            'fundingTime': int((datetime.now() - timedelta(days=1)).timestamp() * 1000),
            'symbol': 'BTCUSD',
            'fundingRate': '0.0002'
        }
    ]
    
    result = detector.get_funding_history('BTCUSD')
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    mock_client.futures_funding_rate.assert_called_once_with(
        symbol='BTCUSD',
        startTime=int((datetime.now() - timedelta(days=7)).timestamp() * 1000),
        endTime=int(datetime.now().timestamp() * 1000),
        limit=1000
    )