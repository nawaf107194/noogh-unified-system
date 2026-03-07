import pytest
import numpy as np

class MockMarketRegimeDetector:
    def is_ranging(self, rsi, atr):
        return 30 <= np.mean(rsi) <= 70 and np.std(atr) < 1.5 * np.mean(atr)

@pytest.fixture
def detector():
    return MockMarketRegimeDetector()

# Happy path
def test_is_ranging_happy_path(detector):
    rsi = np.array([40, 50, 60])
    atr = np.array([1.0, 1.1, 1.2])
    assert detector.is_ranging(rsi, atr) == True

# Edge cases
def test_is_ranging_empty_input(detector):
    rsi = np.array([])
    atr = np.array([])
    with pytest.raises(ValueError):
        detector.is_ranging(rsi, atr)

def test_is_ranging_none_input(detector):
    with pytest.raises(TypeError):
        detector.is_ranging(None, None)

def test_is_ranging_boundary_conditions(detector):
    rsi = np.array([30, 70])
    atr = np.array([1.0, 1.0])
    assert detector.is_ranging(rsi, atr) == True

# Error cases
def test_is_ranging_invalid_input_type(detector):
    rsi = "not an array"
    atr = [1, 2, 3]
    with pytest.raises(TypeError):
        detector.is_ranging(rsi, atr)

def test_is_ranging_invalid_atr_std(detector):
    rsi = np.array([40, 50, 60])
    atr = np.array([2.0, 2.1, 2.2])
    assert detector.is_ranging(rsi, atr) == False

# Since the function is synchronous, there's no need to test async behavior.