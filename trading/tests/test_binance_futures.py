import pytest

from trading.binance_futures import BinanceFuturesClient
from binance.exceptions import BinanceAPIException

class MockBinanceAPIClient:
    def __init__(self):
        self.success = True

    def futures_change_leverage(self, symbol: str, leverage: int) -> Dict:
        if not self.success:
            raise BinanceAPIException('Mock error')
        return {
            'symbol': symbol,
            'leverage': leverage,
            'maxNotionalValue': 10000
        }

def test_change_leverage_happy_path():
    client = MockBinanceAPIClient()
    binance_client = BinanceFuturesClient(client, max_leverage=10, api_key='test_key', read_only=False)
    result = binance_client.change_leverage('BTCUSDT', 5)
    assert result == {
        'symbol': 'BTCUSDT',
        'leverage': 5,
        'max_notional_value': 10000.0
    }

def test_change_leverage_read_only_mode():
    client = MockBinanceAPIClient()
    binance_client = BinanceFuturesClient(client, max_leverage=10, api_key='test_key', read_only=True)
    result = binance_client.change_leverage('BTCUSDT', 5)
    assert result == {'error': 'Read-only mode enabled'}

def test_change_leverage_invalid_leverage():
    client = MockBinanceAPIClient()
    binance_client = BinanceFuturesClient(client, max_leverage=10, api_key='test_key', read_only=False)
    result = binance_client.change_leverage('BTCUSDT', 20)
    assert result == {'error': 'Leverage 20x exceeds safety limit of 10x'}

def test_change_leverage_no_api_key():
    client = MockBinanceAPIClient()
    binance_client = BinanceFuturesClient(client, max_leverage=10, api_key=None, read_only=False)
    result = binance_client.change_leverage('BTCUSDT', 5)
    assert result == {'error': 'API key not configured'}

def test_change_leverage_api_error():
    client = MockBinanceAPIClient()
    client.success = False
    binance_client = BinanceFuturesClient(client, max_leverage=10, api_key='test_key', read_only=False)
    with pytest.raises(BinanceAPIException) as exc_info:
        binance_client.change_leverage('BTCUSDT', 5)
    assert str(exc_info.value) == 'Mock error'