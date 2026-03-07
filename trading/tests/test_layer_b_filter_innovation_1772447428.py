import pytest
from trading.layer_b_filter import statistical_alpha_filter
import numpy as np
import math

@pytest.fixture
def setup_normal():
    return {
        "atr": 0.5,
        "volume": 10000,
        "taker_buy_ratio": 0.6,
        "rsi": 48.0,
        "signal": "LONG"
    }

@pytest.fixture
def setup_edge_cases():
    return [
        {"atr": None, "volume": 50000, "taker_buy_ratio": 0.4, "rsi": 50.0, "signal": "SHORT"},
        {"atr": 1.0, "volume": 0, "taker_buy_ratio": 0.8, "rsi": 60.0, "signal": "LONG"},
        {"atr": -0.2, "volume": 5000, "taker_buy_ratio": 0.3, "rsi": 45.0, "signal": "LONG"}
    ]

@pytest.fixture
def setup_invalid_inputs():
    return [
        {"atr": "not a number", "volume": 10000, "taker_buy_ratio": 0.5, "rsi": 50.0, "signal": "LONG"},
        {"atr": 0.5, "volume": None, "taker_buy_ratio": 0.5, "rsi": 50.0, "signal": "LONG"},
        {"atr": 0.5, "volume": 10000, "taker_buy_ratio": None, "rsi": 50.0, "signal": "LONG"}
    ]

def test_happy_path(setup_normal):
    result = statistical_alpha_filter(setup_normal)
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert isinstance(result[0], bool)
    assert isinstance(result[1], float)
    assert isinstance(result[2], str)

def test_edge_cases(setup_edge_cases):
    for setup in setup_edge_cases:
        result = statistical_alpha_filter(setup)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], bool)
        assert isinstance(result[1], float)
        assert isinstance(result[2], str)

def test_invalid_inputs(setup_invalid_inputs):
    for setup in setup_invalid_inputs:
        result = statistical_alpha_filter(setup)
        assert result is False or result is None, f"Expected None or False for invalid input: {setup}"