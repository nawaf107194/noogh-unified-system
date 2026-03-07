import pytest

class MockPriceData:
    def __init__(self, price_data):
        self.price_data = price_data
        self.lookback = 5
        self.resistance_levels = []
        self.support_levels = []

    def detect_swings(self):
        """
        Detects swing highs and lows within the lookback period.
        """
        for i in range(self.lookback, len(self.price_data)):
            high = max(self.price_data[i-self.lookback:i])
            low = min(self.price_data[i-self.lookback:i])
            if self.price_data[i] == high:
                self.resistance_levels.append(high)
            elif self.price_data[i] == low:
                self.support_levels.append(low)

# Happy path
def test_detect_swings_happy_path():
    mock_data = MockPriceData([10, 20, 30, 40, 50, 60, 70])
    mock_data.detect_swings()
    assert mock_data.resistance_levels == [70]
    assert mock_data.support_levels == []

# Edge cases
def test_detect_swings_empty_data():
    mock_data = MockPriceData([])
    mock_data.detect_swings()
    assert mock_data.resistance_levels == []
    assert mock_data.support_levels == []

def test_detect_swings_single_point():
    mock_data = MockPriceData([10])
    mock_data.lookback = 1
    mock_data.detect_swings()
    assert mock_data.resistance_levels == []
    assert mock_data.support_levels == []

# Error cases (assuming no explicit error handling)
def test_detect_swings_negative_lookback():
    mock_data = MockPriceData([10, 20, 30])
    mock_data.lookback = -5
    mock_data.detect_swings()
    assert mock_data.resistance_levels == []
    assert mock_data.support_levels == []

# Async behavior (not applicable for this synchronous function)