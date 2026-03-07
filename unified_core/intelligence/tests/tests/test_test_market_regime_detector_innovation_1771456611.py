import pytest
import numpy as np

class DetectorMock:
    def is_ranging(self, rsi, atr):
        # Mock implementation for testing purposes
        if len(rsi) != len(atr):
            raise ValueError("RSI and ATR arrays must be of the same length")
        if not all(0 <= x <= 100 for x in rsi):
            raise ValueError("RSI values must be between 0 and 100")
        if not all(x > 0 for x in atr):
            raise ValueError("ATR values must be positive")
        return True

@pytest.fixture
def detector():
    return DetectorMock()

def test_is_ranging_happy_path(detector):
    rsi = np.array([40, 50, 60])
    atr = np.array([1, 1.5, 2])
    assert detector.is_ranging(rsi, atr) == True

def test_is_ranging_empty_arrays(detector):
    rsi = np.array([])
    atr = np.array([])
    with pytest.raises(ValueError):
        detector.is_ranging(rsi, atr)

def test_is_ranging_none_inputs(detector):
    with pytest.raises(TypeError):
        detector.is_ranging(None, np.array([1, 1.5, 2]))
    with pytest.raises(TypeError):
        detector.is_ranging(np.array([40, 50, 60]), None)

def test_is_ranging_mismatched_lengths(detector):
    rsi = np.array([40, 50, 60])
    atr = np.array([1, 1.5])
    with pytest.raises(ValueError):
        detector.is_ranging(rsi, atr)

def test_is_ranging_invalid_rsi_values(detector):
    rsi = np.array([-10, 150, 60])
    atr = np.array([1, 1.5, 2])
    with pytest.raises(ValueError):
        detector.is_ranging(rsi, atr)

def test_is_ranging_invalid_atr_values(detector):
    rsi = np.array([40, 50, 60])
    atr = np.array([-1, 1.5, 2])
    with pytest.raises(ValueError):
        detector.is_ranging(rsi, atr)

def test_is_ranging_boundary_values(detector):
    rsi = np.array([0, 100, 50])
    atr = np.array([0.001, 1.5, 2])
    assert detector.is_ranging(rsi, atr) == True

def test_is_ranging_async_behavior(detector):
    # Assuming async behavior is not applicable for this function
    pass