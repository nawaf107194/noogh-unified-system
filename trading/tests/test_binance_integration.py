import pytest
from binance.exceptions import BinanceAPIException
from unittest.mock import patch

class MockBinanceClient:
    def get_symbol_info(self, symbol: str):
        if symbol == 'BTCUSDT':
            return {
                'symbol': 'BTCUSDT',
                'status': 'TRADING',
                'baseAsset': 'BTC',
                'quoteAsset': 'USDT',
                'filters': [{'filterType': 'PRICE_FILTER'}]
            }
        else:
            raise BinanceAPIException("Symbol not found")

def test_get_symbol_info_happy_path():
    client = MockBinanceClient()
    with patch.object(BinanceIntegration, '_rate_limit', return_value=None):
        integration = BinanceIntegration(client=client)
        result = integration.get_symbol_info('BTCUSDT')
    assert result == {
        'symbol': 'BTCUSDT',
        'status': 'TRADING',
        'base_asset': 'BTC',
        'quote_asset': 'USDT',
        'filters': [{'filterType': 'PRICE_FILTER'}]
    }

def test_get_symbol_info_edge_case_empty_input():
    client = MockBinanceClient()
    with patch.object(BinanceIntegration, '_rate_limit', return_value=None):
        integration = BinanceIntegration(client=client)
        result = integration.get_symbol_info('')
    assert result == {}

def test_get_symbol_info_edge_case_none_input():
    client = MockBinanceClient()
    with patch.object(BinanceIntegration, '_rate_limit', return_value=None):
        integration = BinanceIntegration(client=client)
        result = integration.get_symbol_info(None)
    assert result == {}

def test_get_symbol_info_error_case_invalid_symbol():
    client = MockBinanceClient()
    with patch.object(BinanceIntegration, '_rate_limit', return_value=None):
        integration = BinanceIntegration(client=client)
        result = integration.get_symbol_info('INVALIDSYMBOL')
    assert result == {}