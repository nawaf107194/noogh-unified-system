import pytest

class MockTradingFeature:
    def __init__(self, price_data, lookback):
        self.price_data = price_data
        self.lookback = lookback
        self.resistance_levels = []
        self.support_levels = []

    def detect_swings(self):
        for i in range(self.lookback, len(self.price_data)):
            high = max(self.price_data[i-self.lookback:i])
            low = min(self.price_data[i-self.lookback:i])
            if self.price_data[i] == high:
                self.resistance_levels.append(high)
            elif self.price_data[i] == low:
                self.support_levels.append(low)

@pytest.fixture
def trading_feature():
    return MockTradingFeature([100, 102, 101, 103, 104, 102, 101], 3)

def test_happy_path(trading_feature):
    trading_feature.detect_swings()
    assert trading_feature.resistance_levels == [103, 104]
    assert trading_feature.support_levels == [101]

def test_empty_price_data():
    trading_feature = MockTradingFeature([], 3)
    trading_feature.detect_swings()
    assert trading_feature.resistance_levels == []
    assert trading_feature.support_levels == []

def test_none_price_data():
    with pytest.raises(TypeError):
        MockTradingFeature(None, 3).detect_swings()

def test_single_element_price_data():
    trading_feature = MockTradingFeature([100], 3)
    trading_feature.detect_swings()
    assert trading_feature.resistance_levels == []
    assert trading_feature.support_levels == []

def test_lookback_greater_than_price_data_length():
    trading_feature = MockTradingFeature([100, 101, 102], 4)
    trading_feature.detect_swings()
    assert trading_feature.resistance_levels == []
    assert trading_feature.support_levels == []

def test_invalid_lookback_type():
    with pytest.raises(TypeError):
        MockTradingFeature([100, 101, 102], '3').detect_swings()

def test_negative_lookback():
    with pytest.raises(ValueError):
        MockTradingFeature([100, 101, 102], -1).detect_swings()

def test_non_numeric_price_data():
    with pytest.raises(TypeError):
        MockTradingFeature(['a', 'b', 'c'], 3).detect_swings()

def test_async_behavior():
    # Since the provided function does not involve any asynchronous operations,
    # there is no need to test for async behavior.
    pass