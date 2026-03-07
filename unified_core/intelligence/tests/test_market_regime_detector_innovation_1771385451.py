import pytest
import numpy as np

class MarketRegimeDetector:
    def is_ranging(self, rsi, atr):
        return 30 <= np.mean(rsi) <= 70 and np.std(atr) < 1.5 * np.mean(atr)

@pytest.fixture
def detector():
    return MarketRegimeDetector()

# Happy path (normal inputs)
def test_is_ranging_happy_path(detector):
    rsi = np.array([40, 50, 60])
    atr = np.array([1.2, 1.3, 1.4])
    assert detector.is_ranging(rsi, atr) == True

# Edge case (empty input)
def test_is_ranging_empty_input(detector):
    rsi = np.array([])
    atr = np.array([])
    with pytest.raises(ValueError):
        detector.is_ranging(rsi, atr)

# Edge case (None input)
def test_is_ranging_none_input(detector):
    with pytest.raises(TypeError):
        detector.is_ranging(None, None)

# Edge case (boundary conditions)
def test_is_ranging_boundary_conditions(detector):
    rsi = np.array([30, 70, 50])
    atr = np.array([1.0, 1.0, 1.0])
    assert detector.is_ranging(rsi, atr) == True

    rsi = np.array([29, 71, 50])
    atr = np.array([1.0, 1.0, 1.0])
    assert detector.is_ranging(rsi, atr) == False

# Error case (invalid inputs)
def test_is_ranging_invalid_inputs(detector):
    rsi = "not an array"
    atr = "not an array"
    with pytest.raises(TypeError):
        detector.is_ranging(rsi, atr)

    rsi = [1, 2, 3]
    atr = [1, 2, 3]
    with pytest.raises(TypeError):
        detector.is_ranging(rsi, atr)

# Async behavior is not applicable for this function as it does not involve asynchronous operations.