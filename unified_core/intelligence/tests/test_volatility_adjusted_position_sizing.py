import pytest
import numpy as np

class MockVolatilityAdjustedPositionSizing:
    def __init__(self, min_leverage, base_leverage, max_leverage, price_data):
        self.min_leverage = min_leverage
        self.base_leverage = base_leverage
        self.max_leverage = max_leverage
        self.price_data = price_data

    def adjust_position_size(self, volatility, current_price):
        normalized_volatility = np.interp(volatility, [0, np.max(self.price_data)], [self.min_leverage, self.base_leverage])
        adjusted_leverage = np.clip(normalized_volatility, self.min_leverage, self.max_leverage)
        position_size = current_price * adjusted_leverage
        return adjusted_leverage, position_size

@pytest.fixture
def mock_volatility_adjusted_position_sizing():
    min_leverage = 0.5
    base_leverage = 2.0
    max_leverage = 3.0
    price_data = np.array([100, 150, 200, 250])
    return MockVolatilityAdjustedPositionSizing(min_leverage, base_leverage, max_leverage, price_data)

# Happy path
def test_adjust_position_size_happy_path(mock_volatility_adjusted_position_sizing):
    volatility = 175
    current_price = 150
    expected_leverage = 1.5
    expected_position_size = 225
    assert mock_volatility_adjusted_position_sizing.adjust_position_size(volatility, current_price) == (expected_leverage, expected_position_size)

# Edge cases
def test_adjust_position_size_min_volatility(mock_volatility_adjusted_position_sizing):
    volatility = 0
    current_price = 150
    expected_leverage = 0.5
    expected_position_size = 75
    assert mock_volatility_adjusted_position_sizing.adjust_position_size(volatility, current_price) == (expected_leverage, expected_position_size)

def test_adjust_position_size_max_volatility(mock_volatility_adjusted_position_sizing):
    volatility = 250
    current_price = 150
    expected_leverage = 3.0
    expected_position_size = 450
    assert mock_volatility_adjusted_position_sizing.adjust_position_size(volatility, current_price) == (expected_leverage, expected_position_size)

def test_adjust_position_size_with_none_values(mock_volatility_adjusted_position_sizing):
    with pytest.raises(TypeError):
        mock_volatility_adjusted_position_sizing.adjust_position_size(None, 150)
    with pytest.raises(TypeError):
        mock_volatility_adjusted_position_sizing.adjust_position_size(175, None)

# Error cases
def test_adjust_position_size_with_invalid_volatility(mock_volatility_adjusted_position_sizing):
    with pytest.raises(ValueError):
        mock_volatility_adjusted_position_sizing.adjust_position_size(-1, 150)

def test_adjust_position_size_with_invalid_current_price(mock_volatility_adjusted_position_sizing):
    with pytest.raises(ValueError):
        mock_volatility_adjusted_position_sizing.adjust_position_size(175, -1)

# Async behavior is not applicable in this case since the function does not involve any asynchronous operations.