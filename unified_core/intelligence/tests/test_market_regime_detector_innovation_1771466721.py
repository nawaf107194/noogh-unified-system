import pytest
import numpy as np

class MockMarketRegimeDetector:
    def is_trending(self, rsi, atr):
        return np.mean(rsi) > 70 or np.mean(rsi) < 30

@pytest.fixture
def detector():
    return MockMarketRegimeDetector()

# Happy path (normal inputs)
def test_is_trending_happy_path(detector):
    rsi = [80, 85, 90]
    atr = [1.2, 1.5, 1.8]
    assert detector.is_trending(rsi, atr) == True

def test_is_trending_happy_path_not_trending(detector):
    rsi = [50, 55, 60]
    atr = [1.2, 1.5, 1.8]
    assert detector.is_trending(rsi, atr) == False

# Edge cases (empty, None, boundaries)
def test_is_trending_empty_rsi(detector):
    rsi = []
    atr = [1.2, 1.5, 1.8]
    with pytest.raises(ValueError):
        detector.is_trending(rsi, atr)

def test_is_trending_none_rsi(detector):
    rsi = None
    atr = [1.2, 1.5, 1.8]
    with pytest.raises(TypeError):
        detector.is_trending(rsi, atr)

def test_is_trending_boundary_case_high(detector):
    rsi = [70, 70, 70]
    atr = [1.2, 1.5, 1.8]
    assert detector.is_trending(rsi, atr) == False

def test_is_trending_boundary_case_low(detector):
    rsi = [30, 30, 30]
    atr = [1.2, 1.5, 1.8]
    assert detector.is_trending(rsi, atr) == False

# Error cases (invalid inputs)
def test_is_trending_invalid_input_type(detector):
    rsi = "80"
    atr = [1.2, 1.5, 1.8]
    with pytest.raises(TypeError):
        detector.is_trending(rsi, atr)

def test_is_trending_invalid_atr_type(detector):
    rsi = [80, 85, 90]
    atr = "1.2"
    with pytest.raises(TypeError):
        detector.is_trending(rsi, atr)

# Async behavior (if applicable)
# Since the given function does not involve any asynchronous operations,
# there's no need to test async behavior in this context.