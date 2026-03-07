import pytest
import numpy as np
from unified_core.intelligence.market_regime_detector import MarketRegimeDetector

@pytest.fixture
def detector():
    return MarketRegimeDetector()

def test_is_trending_happy_path(detector):
    rsi = np.array([75, 68, 72, 71])
    atr = np.array([0.5, 0.4, 0.6, 0.55])
    assert detector.is_trending(rsi, atr) == True

def test_is_trending_edge_case_empty_rsi(detector):
    rsi = np.array([])
    atr = np.array([0.5, 0.4, 0.6, 0.55])
    assert detector.is_trending(rsi, atr) == False

def test_is_trending_edge_case_empty_atr(detector):
    rsi = np.array([75, 68, 72, 71])
    atr = np.array([])
    assert detector.is_trending(rsi, atr) == False

def test_is_trending_edge_case_rsi_boundary(detector):
    rsi = np.array([30, 30, 30, 30])
    atr = np.array([0.5, 0.4, 0.6, 0.55])
    assert detector.is_trending(rsi, atr) == False

def test_is_trending_edge_case_atr_boundary(detector):
    rsi = np.array([75, 68, 72, 71])
    atr = np.array([0.4, 0.4, 0.4, 0.4])
    assert detector.is_trending(rsi, atr) == False

def test_is_trending_error_case_invalid_rsi_type(detector):
    rsi = "not a numpy array"
    atr = np.array([0.5, 0.4, 0.6, 0.55])
    result = detector.is_trending(rsi, atr)
    assert result is False

def test_is_trending_error_case_invalid_atr_type(detector):
    rsi = np.array([75, 68, 72, 71])
    atr = "not a numpy array"
    result = detector.is_trending(rsi, atr)
    assert result is False