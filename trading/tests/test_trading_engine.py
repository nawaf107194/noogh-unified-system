import pytest

from trading.trading_engine import TradingEngine

# Mocking dependencies for testing
class MockTradingEngine(TradingEngine):
    @staticmethod
    def get_market_data(symbol, interval, limit):
        if symbol == 'BTCUSDT':
            return pd.DataFrame({'close': [100] * 50})
        elif symbol == 'ETHUSDT':
            return pd.DataFrame({'close': [200, 300, 400] * 16 + [400]})
        else:
            return pd.DataFrame()

@pytest.fixture
def trading_engine():
    return MockTradingEngine()

def test_get_btc_correlation_happy_path(trading_engine):
    correlation = trading_engine.get_btc_correlation('ETHUSDT')
    assert -1 <= correlation <= 1

def test_get_btc_correlation_empty_data(trading_engine):
    correlation = trading_engine.get_btc_correlation('LTCUSDT')
    assert correlation == 0.0

def test_get_btc_correlation_boundary_period(trading_engine):
    correlation = trading_engine.get_btc_correlation('ETHUSDT', period=5)
    assert -1 <= correlation <= 1

def test_get_btc_correlation_invalid_symbol(trading_engine):
    correlation = trading_engine.get_btc_correlation('INVALID')
    assert correlation == 0.0