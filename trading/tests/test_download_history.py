import pytest
from datetime import datetime, timedelta
import pandas as pd

from trading.download_history import download_historical_data

@pytest.fixture()
def client():
    return MagicMock()

def test_happy_path(client):
    # Mock the client to return some data
    client.futures_historical_klines.side_effect = lambda *args: [
        [1633072800000, '150.00000000', '150.00000000', '150.00000000', '150.00000000', '2000.00000000', 1633072859999, '300000.00000000', 100, '100.00000000', '100.00000000', '0']
    ]
    
    df = download_historical_data(symbol='BTCUSDT', interval='1m', start_str='2021-10-01T00:00:00Z')
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert 'timestamp' in df.columns
    assert 'open' in df.columns
    assert 'high' in df.columns
    assert 'low' in df.columns
    assert 'close' in df.columns
    assert 'volume' in df.columns

def test_edge_case_empty(client):
    # Mock the client to return an empty list
    client.futures_historical_klines.side_effect = lambda *args: []
    
    df = download_historical_data(symbol='BTCUSDT', interval='1m', start_str='2021-10-01T00:00:00Z')
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0

def test_edge_case_none(client):
    # Mock the client to return None
    client.futures_historical_klines.side_effect = lambda *args: None
    
    df = download_historical_data(symbol='BTCUSDT', interval='1m', start_str='2021-10-01T00:00:00Z')
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0

def test_error_case_invalid_symbol(client):
    # Mock the client to raise an exception for an invalid symbol
    client.futures_historical_klines.side_effect = BinanceAPIException(message='Invalid symbol')
    
    df = download_historical_data(symbol='INVALID', interval='1m', start_str='2021-10-01T00:00:00Z')
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0

def test_error_case_invalid_interval(client):
    # Mock the client to raise an exception for an invalid interval
    client.futures_historical_klines.side_effect = BinanceAPIException(message='Invalid interval')
    
    df = download_historical_data(symbol='BTCUSDT', interval='INVALID', start_str='2021-10-01T00:00:00Z')
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0

def test_error_case_invalid_start_str(client):
    # Mock the client to raise an exception for an invalid start string
    client.futures_historical_klines.side_effect = BinanceAPIException(message='Invalid start time format')
    
    df = download_historical_data(symbol='BTCUSDT', interval='1m', start_str='INVALID')
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0

def test_error_case_invalid_end_str(client):
    # Mock the client to raise an exception for an invalid end string
    client.futures_historical_klines.side_effect = BinanceAPIException(message='Invalid end time format')
    
    df = download_historical_data(symbol='BTCUSDT', interval='1m', start_str='2021-10-01T00:00:00Z', end_str='INVALID')
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0