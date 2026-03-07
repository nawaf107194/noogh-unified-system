import pytest
import numpy as np

class DetectorMock:
    def is_ranging(self, rsi, atr):
        # Mock implementation of is_ranging method
        if not isinstance(rsi, np.ndarray) or not isinstance(atr, np.ndarray):
            raise ValueError("RSI and ATR must be numpy arrays")
        if len(rsi) != len(atr):
            raise ValueError("RSI and ATR arrays must have the same length")
        if np.any(rsi < 0) or np.any(rsi > 100):
            raise ValueError("RSI values must be between 0 and 100")
        if np.any(atr < 0):
            raise ValueError("ATR values must be non-negative")
        
        # Simplified logic for demonstration purposes
        return np.all((rsi >= 30) & (rsi <= 70)) and np.all((atr >= 1) & (atr <= 1.5))

@pytest.fixture
def detector():
    return DetectorMock()

def test_is_ranging_happy_path(detector):
    rsi = np.array([40, 60])
    atr = np.array([1.2, 1.3])
    assert detector.is_ranging(rsi, atr) == True

def test_is_ranging_edge_cases_empty_arrays(detector):
    rsi = np.array([])
    atr = np.array([])
    with pytest.raises(ValueError, match="RSI and ATR arrays must have the same length"):
        detector.is_ranging(rsi, atr)

def test_is_ranging_edge_cases_none_arrays(detector):
    rsi = None
    atr = None
    with pytest.raises(ValueError, match="RSI and ATR must be numpy arrays"):
        detector.is_ranging(rsi, atr)

def test_is_ranging_edge_cases_boundary_values(detector):
    rsi = np.array([30, 70])
    atr = np.array([1, 1.5])
    assert detector.is_ranging(rsi, atr) == False

def test_is_ranging_error_cases_invalid_length(detector):
    rsi = np.array([30, 70])
    atr = np.array([1])
    with pytest.raises(ValueError, match="RSI and ATR arrays must have the same length"):
        detector.is_ranging(rsi, atr)

def test_is_ranging_error_cases_invalid_rsi_values(detector):
    rsi = np.array([-10, 110])
    atr = np.array([1, 1.5])
    with pytest.raises(ValueError, match="RSI values must be between 0 and 100"):
        detector.is_ranging(rsi, atr)

def test_is_ranging_error_cases_invalid_atr_values(detector):
    rsi = np.array([40, 60])
    atr = np.array([-1, 1.5])
    with pytest.raises(ValueError, match="ATR values must be non-negative"):
        detector.is_ranging(rsi, atr)

# Assuming async behavior is not applicable to this function, no async tests are included.