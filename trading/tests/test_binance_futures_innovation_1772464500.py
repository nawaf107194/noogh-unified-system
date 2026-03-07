import pytest
from trading.binance_futures import BinanceFutures

@pytest.fixture
def mock_client():
    class MockClient:
        def futures_create_order(self, *args, **kwargs):
            return {'orderId': '12345', 'symbol': 'BTCUSDT', 'side': 'SELL', 'origQty': 0.001, 'status': 'FILLED', 'updateTime': 1672531200000}
        
        def get_positions(self, *args, **kwargs):
            return [{'position_amount': -0.001, 'unrealized_pnl': -10}]
        
        def cancel_all_orders(self, *args, **kwargs):
            pass
    
    return MockClient()

def test_close_position_happy_path(mock_client):
    client = BinanceFutures(api_key='fake_api_key', api_secret='fake_api_secret', read_only=False)
    client.client = mock_client
    result = client.close_position('BTCUSDT')
    assert result == {
        'success': True,
        'order_id': '12345',
        'symbol': 'BTCUSDT',
        'side': 'SELL',
        'quantity': 0.001,
        'status': 'FILLED',
        'pnl': -10,
        'time': 1672531200000
    }

def test_close_position_read_only_mode(mock_client):
    client = BinanceFutures(api_key='fake_api_key', api_secret='fake_api_secret', read_only=True)
    client.client = mock_client
    result = client.close_position('BTCUSDT')
    assert result == {'error': '🔒 Trading disabled - read-only mode enabled'}

def test_close_position_no_api_key(mock_client):
    client = BinanceFutures(api_key=None, api_secret='fake_api_secret', read_only=False)
    client.client = mock_client
    result = client.close_position('BTCUSDT')
    assert result == {'error': 'API key not configured'}

def test_close_position_no_positions(mock_client):
    class MockClient:
        def futures_create_order(self, *args, **kwargs):
            return {'orderId': '12345', 'symbol': 'BTCUSDT', 'side': 'SELL', 'origQty': 0.001, 'status': 'FILLED', 'updateTime': 1672531200000}
        
        def get_positions(self, *args, **kwargs):
            return []
        
        def cancel_all_orders(self, *args, **kwargs):
            pass
    
    client = BinanceFutures(api_key='fake_api_key', api_secret='fake_api_secret', read_only=False)
    client.client = MockClient()
    result = client.close_position('BTCUSDT')
    assert result == {'error': 'No open position for BTCUSDT'}

def test_close_position_no_position_to_close(mock_client):
    class MockClient:
        def futures_create_order(self, *args, **kwargs):
            return {'orderId': '12345', 'symbol': 'BTCUSDT', 'side': 'SELL', 'origQty': 0.001, 'status': 'FILLED', 'updateTime': 1672531200000}
        
        def get_positions(self, *args, **kwargs):
            return [{'position_amount': 0.0, 'unrealized_pnl': -10}]
        
        def cancel_all_orders(self, *args, **kwargs):
            pass
    
    client = BinanceFutures(api_key='fake_api_key', api_secret='fake_api_secret', read_only=False)
    client.client = MockClient()
    result = client.close_position('BTCUSDT')
    assert result == {'error': 'No position to close for BTCUSDT'}

def test_close_position_binance_api_exception(mock_client):
    class MockClient:
        def futures_create_order(self, *args, **kwargs):
            raise BinanceAPIException('Mocked API error')
        
        def get_positions(self, *args, **kwargs):
            return [{'position_amount': -0.001, 'unrealized_pnl': -10}]
        
        def cancel_all_orders(self, *args, **kwargs):
            pass
    
    client = BinanceFutures(api_key='fake_api_key', api_secret='fake_api_secret', read_only=False)
    client.client = MockClient()
    result = client.close_position('BTCUSDT')
    assert result == {'error': 'Mocked API error'}