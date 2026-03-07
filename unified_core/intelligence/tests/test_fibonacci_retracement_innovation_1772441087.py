import pytest

from unified_core.intelligence.fibonacci_retracement import FibonacciRetracement

@pytest.fixture
def fib_retracement():
    return FibonacciRetracement()

class TestFibonacciRetracement:

    def test_get_fib_levels_happy_path(self, fib_retracement):
        # Arrange
        expected = [0.236, 0.382, 0.5, 0.618, 0.764, 0.886]
        
        # Act
        result = fib_retracement.get_fib_levels()
        
        # Assert
        assert result == expected

    def test_get_fib_levels_empty(self, fib_retracement):
        # Arrange
        fib_retracement.fib_levels = []
        
        # Act
        result = fib_retracement.get_fib_levels()
        
        # Assert
        assert result == []

    def test_get_fib_levels_none(self, fib_retracement):
        # Arrange
        fib_retracement.fib_levels = None
        
        # Act
        result = fib_retracement.get_fib_levels()
        
        # Assert
        assert result is None

    def test_get_fib_levels_boundary_values(self, fib_retracement):
        # Arrange
        boundary_values = [0, 1, -1]
        for value in boundary_values:
            fib_retracement.fib_levels = [value]
            
            # Act
            result = fib_retracement.get_fib_levels()
            
            # Assert
            assert result == [value]

    def test_get_fib_levels_invalid_input(self, fib_retracement):
        # Arrange
        invalid_values = ["string", {"key": "value"}, True]
        for value in invalid_values:
            fib_retracement.fib_levels = value
            
            # Act
            result = fib_retracement.get_fib_levels()
            
            # Assert
            assert result is None