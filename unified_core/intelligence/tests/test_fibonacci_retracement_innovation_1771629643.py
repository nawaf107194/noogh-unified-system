import pytest

class TestFibonacciRetracement:

    @pytest.fixture
    def fib_retracement_instance(self):
        return FibonacciRetracement(100, 50)

    def test_happy_path(self, fib_retracement_instance):
        assert fib_retracement_instance.high_price == 100
        assert fib_retracement_instance.low_price == 50
        assert len(fib_retracement_instance.fib_levels) > 0

    def test_edge_case_empty_high_price(self):
        with pytest.raises(TypeError):
            FibonacciRetracement('', 50)

    def test_edge_case_none_low_price(self):
        with pytest.raises(TypeError):
            FibonacciRetracement(100, None)

    def test_error_case_invalid_high_price_type(self):
        with pytest.raises(TypeError):
            FibonacciRetracement('100', 50)

    def test_error_case_invalid_low_price_type(self):
        with pytest.raises(TypeError):
            FibonacciRetracement(100, '50')

    def test_edge_case_boundary_values(self):
        with pytest.raises(ValueError):
            fib_retracement = FibonacciRetracement(50, 50)

class FibonacciRetracement:
    def __init__(self, high_price, low_price):
        if not isinstance(high_price, (int, float)) or not isinstance(low_price, (int, float)):
            raise TypeError("High and Low prices must be numbers")
        if high_price <= low_price:
            raise ValueError("High price must be greater than Low price")
        
        self.high_price = high_price
        self.low_price = low_price
        self.fib_levels = self.calculate_fib_levels()

    def calculate_fib_levels(self):
        distance = self.high_price - self.low_price
        levels = [
            round(self.low_price + 0.236 * distance, 4),
            round(self.low_price + 0.382 * distance, 4),
            round(self.low_price + 0.500 * distance, 4),
            round(self.low_price + 0.618 * distance, 4),
            round(self.low_price + 0.786 * distance, 4)
        ]
        return levels