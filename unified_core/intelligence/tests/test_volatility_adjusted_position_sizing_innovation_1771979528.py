import numpy as np
import pytest

from unified_core.intelligence.volatility_adjusted_position_sizing import VolatilityCalculator

def test_calculate_volatility_happy_path():
    calculator = VolatilityCalculator()
    price_data = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118,
                  120, 122, 124, 126, 128, 130, 132, 134, 136, 138, 140]
    expected_volatility = np.std(price_data[-20:], ddof=1)
    assert calculator.calculate_volatility(price_data) == expected_volatility

def test_calculate_volatility_empty_input():
    calculator = VolatilityCalculator()
    price_data = []
    assert calculator.calculate_volatility(price_data) is None

def test_calculate_volatility_none_input():
    calculator = VolatilityCalculator()
    price_data = None
    assert calculator.calculate_volatility(price_data) is None

def test_calculate_volatility_single_period():
    calculator = VolatilityCalculator()
    price_data = [100]
    assert calculator.calculate_volatility(price_data) is None

def test_calculate_volatility_boundary_condition():
    calculator = VolatilityCalculator()
    price_data = list(range(20))
    expected_volatility = np.std(price_data, ddof=1)
    assert calculator.calculate_volatility(price_data) == expected_volatility