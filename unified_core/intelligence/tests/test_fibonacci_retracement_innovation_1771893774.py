import pytest

class FibonacciRetracementDummy:
    def __init__(self, high_price, low_price):
        self.high_price = high_price
        self.low_price = low_price

    def calculate_fib_levels(self):
        diff = self.high_price - self.low_price
        levels = {
            '0%': self.high_price,
            '23.6%': self.high_price - diff * 0.236,
            '38.2%': self.high_price - diff * 0.382,
            '50%': self.high_price - diff * 0.5,
            '61.8%': self.high_price - diff * 0.618,
            '100%': self.low_price
        }
        return levels

def test_happy_path():
    retracement = FibonacciRetracementDummy(10, 2)
    expected_levels = {
        '0%': 10,
        '23.6%': 7.64,
        '38.2%': 5.18,
        '50%': 3.0,
        '61.8%': 0.82,
        '100%': 2
    }
    assert retracement.calculate_fib_levels() == expected_levels

def test_edge_case_high_equal_low():
    retracement = FibonacciRetracementDummy(5, 5)
    expected_levels = {
        '0%': 5,
        '23.6%': 5,
        '38.2%': 5,
        '50%': 5,
        '61.8%': 5,
        '100%': 5
    }
    assert retracement.calculate_fib_levels() == expected_levels

def test_edge_case_high_less_than_low():
    retracement = FibonacciRetracementDummy(3, 7)
    with pytest.raises(ValueError):
        retracement.calculate_fib_levels()

def test_error_case_none_input():
    retracement = FibonacciRetracementDummy(None, None)
    assert retracement.calculate_fib_levels() is None

def test_error_case_invalid_type():
    retracement = FibonacciRetracementDummy('10', '2')
    assert retracement.calculate_fib_levels() is None