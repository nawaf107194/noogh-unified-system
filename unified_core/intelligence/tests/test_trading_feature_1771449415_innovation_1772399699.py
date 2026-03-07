import pytest

from unified_core.intelligence.trading_feature_1771449415 import TradingFeature

def test_normal_inputs():
    price_data = [100, 102, 101, 103]
    feature = TradingFeature(price_data)
    assert feature.price_data == price_data
    assert feature.lookback == 20
    assert feature.support_levels == []
    assert feature.resistance_levels == []

def test_empty_price_data():
    feature = TradingFeature([])
    assert feature.price_data == []
    assert feature.lookback == 20
    assert feature.support_levels == []
    assert feature.resistance_levels == []

def test_none_price_data():
    with pytest.raises(TypeError):
        TradingFeature(None)

def test_negative_lookback():
    with pytest.raises(ValueError):
        TradingFeature([1, 2, 3], -5)

def test_zero_lookback():
    with pytest.raises(ValueError):
        TradingFeature([1, 2, 3], 0)