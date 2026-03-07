import pytest
import numpy as np

class MockMarketRegimeDetector:
    def is_ranging(self, rsi, atr):
        return 30 <= np.mean(rsi) <= 70 and np.std(atr) < 1.5 * np.mean(atr)

@pytest.fixture
def detector():
    return MockMarketRegimeDetector()

# Happy path (normal inputs)
def test_is_ranging_happy_path(detector):
    rsi = np.array([40, 50, 60])
    atr = np.array([1, 1.5, 2])
    assert detector.is_ranging(rsi, atr) == True

# Edge cases (empty, None, boundaries)
def test_is_ranging_empty_inputs(detector):
    rsi = np.array([])
    atr = np.array([])
    with pytest.raises(ValueError):
        detector.is_ranging(rsi, atr)

def test_is_ranging_none_inputs(detector):
    rsi = None
    atr = None
    with pytest.raises(TypeError):
        detector.is_ranging(rsi, atr)

def test_is_ranging_boundary_values(detector):
    rsi = np.array([30, 70])
    atr = np.array([1, 1.5])
    assert detector.is_ranging(rsi, atr) == False

# Error cases (invalid inputs)
def test_is_ranging_invalid_input_types(detector):
    rsi = "not an array"
    atr = [1, 2, 3]
    with pytest.raises(TypeError):
        detector.is_ranging(rsi, atr)

def test_is_ranging_non_numeric_values(detector):
    rsi = np.array(["a", "b", "c"])
    atr = np.array([1, 2, 3])
    with pytest.raises(TypeError):
        detector.is_ranging(rsi, atr)

# Since the function is synchronous, there's no async behavior to test.