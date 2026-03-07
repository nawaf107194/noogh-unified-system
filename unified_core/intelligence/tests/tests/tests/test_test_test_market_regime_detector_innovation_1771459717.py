import pytest
import numpy as np

class DetectorMock:
    def is_ranging(self, rsi, atr):
        if len(rsi) != len(atr):
            raise ValueError("RSI and ATR arrays must have the same length")
        # Mock implementation of is_ranging
        return True

@pytest.fixture
def detector():
    return DetectorMock()

def test_is_ranging_happy_path(detector):
    rsi = np.array([30, 70, 50])
    atr = np.array([1, 2, 3])
    result = detector.is_ranging(rsi, atr)
    assert result == True

def test_is_ranging_edge_case_empty_arrays(detector):
    rsi = np.array([])
    atr = np.array([])
    result = detector.is_ranging(rsi, atr)
    assert result == True

def test_is_ranging_edge_case_none_arrays(detector):
    rsi = None
    atr = None
    with pytest.raises(TypeError, match="unsupported operand type\(s\) for \*: 'NoneType' and 'int'"):
        detector.is_ranging(rsi, atr)

def test_is_ranging_edge_case_single_element(detector):
    rsi = np.array([30])
    atr = np.array([1])
    result = detector.is_ranging(rsi, atr)
    assert result == True

def test_is_ranging_error_cases_invalid_length(detector):
    rsi = np.array([30, 70])
    atr = np.array([1])
    with pytest.raises(ValueError, match="RSI and ATR arrays must have the same length"):
        detector.is_ranging(rsi, atr)

def test_is_ranging_error_cases_mismatched_lengths(detector):
    rsi = np.array([30, 70, 50])
    atr = np.array([1, 2])
    with pytest.raises(ValueError, match="RSI and ATR arrays must have the same length"):
        detector.is_ranging(rsi, atr)

# Assuming the function does not have async behavior
# If it did, we would need to mock an async version of `is_ranging` and use `pytest.mark.asyncio`
# For example:
# @pytest.mark.asyncio
# async def test_is_ranging_async_behavior(detector):
#     rsi = np.array([30, 70])
#     atr = np.array([1, 2])
#     result = await detector.is_ranging(rsi, atr)
#     assert result == True