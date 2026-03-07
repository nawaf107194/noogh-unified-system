import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def market_regime_detector():
    class MockMarketRegimeDetector:
        def __init__(self):
            self.regimes = {
                'Bull': lambda rsi, atr: rsi > 70,
                'Bear': lambda rsi, atr: rsi < 30,
                'Range': lambda rsi, atr: 30 <= rsi <= 70
            }
            self.fetch_data = Mock(return_value=[100, 200])
            self.calculate_indicators = Mock(return_value=(50, 15))

        def detect_regime(self, symbol, timeframe='1h'):
            data = self.fetch_data(symbol, timeframe)
            rsi, atr = self.calculate_indicators(data)
            for regime, condition in self.regimes.items():
                if condition(rsi, atr):
                    return regime
            return 'Unknown'
    
    return MockMarketRegimeDetector()

def test_happy_path(market_regime_detector):
    result = market_regime_detector.detect_regime('AAPL', '1h')
    assert result == 'Range'

def test_edge_case_empty_symbol(market_regime_detector):
    with pytest.raises(ValueError, match="Symbol cannot be empty"):
        market_regime_detector.detect_regime('', '1h')

def test_edge_case_none_symbol(market_regime_detector):
    with pytest.raises(TypeError, match="Symbol must be a string"):
        market_regime_detector.detect_regime(None, '1h')

def test_edge_case_boundary_rsi(market_regime_detector):
    market_regime_detector.calculate_indicators.return_value = (30, 15)
    result = market_regime_detector.detect_regime('AAPL', '1h')
    assert result == 'Range'

def test_error_case_invalid_timeframe(market_regime_detector):
    with pytest.raises(ValueError, match="Invalid timeframe format"):
        market_regime_detector.detect_regime('AAPL', 'invalid')

@patch.object(MockMarketRegimeDetector, 'fetch_data', side_effect=Exception("Fetch data failed"))
def test_error_case_fetch_data_exception(mock_fetch_data, market_regime_detector):
    with pytest.raises(Exception, match="Fetch data failed"):
        market_regime_detector.detect_regime('AAPL', '1h')

@patch.object(MockMarketRegimeDetector, 'calculate_indicators', side_effect=Exception("Calculate indicators failed"))
def test_error_case_calculate_indicators_exception(mock_calculate_indicators, market_regime_detector):
    with pytest.raises(Exception, match="Calculate indicators failed"):
        market_regime_detector.detect_regime('AAPL', '1h')

def test_async_behavior_not_applicable(market_regime_detector):
    # Since the given function is synchronous and does not involve any async operations,
    # no specific test is needed for async behavior.
    pass