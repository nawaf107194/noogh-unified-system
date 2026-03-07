import pytest

from unified_core.intelligence.trading_feature_1771449415 import TradingDetector

def test_init_happy_path():
    price_data = [100, 102, 101, 103, 105]
    detector = TradingDetector(price_data)
    assert detector.price_data == price_data
    assert detector.lookback == 20
    assert detector.support_levels == []
    assert detector.resistance_levels == []

def test_init_empty_price_data():
    price_data = []
    detector = TradingDetector(price_data, lookback=10)
    assert detector.price_data == price_data
    assert detector.lookback == 10
    assert detector.support_levels == []
    assert detector.resistance_levels == []

def test_init_none_price_data():
    price_data = None
    detector = TradingDetector(price_data, lookback=15)
    assert detector.price_data is None
    assert detector.lookback == 15
    assert detector.support_levels == []
    assert detector.resistance_levels == []

def test_init_negative_lookback():
    price_data = [100, 102, 101]
    with pytest.raises(ValueError):
        TradingDetector(price_data, lookback=-5)

def test_init_zero_lookback():
    price_data = [100, 102, 101]
    detector = TradingDetector(price_data, lookback=0)
    assert detector.price_data == price_data
    assert detector.lookback == 0
    assert detector.support_levels == []
    assert detector.resistance_levels == []

# Add more tests as needed for other edge cases and error conditions