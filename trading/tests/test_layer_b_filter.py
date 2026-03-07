import pytest
import numpy as np
import math

from trading.layer_b_filter import statistical_alpha_filter

@pytest.fixture
def setup():
    return {
        "atr": 1.2,
        "volume": 1000000,
        "taker_buy_ratio": 0.6,
        "rsi": 45.0,
        "signal": "LONG"
    }

def test_happy_path(setup):
    result = statistical_alpha_filter(setup)
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert isinstance(result[0], bool)
    assert isinstance(result[1], float)
    assert isinstance(result[2], str)

def test_edge_case_empty_setup():
    result = statistical_alpha_filter({})
    assert not result[0]
    assert result[2].startswith("Rejected (")

def test_edge_case_none_signal():
    setup = {
        "atr": 1.2,
        "volume": 1000000,
        "taker_buy_ratio": 0.6,
        "rsi": 45.0,
        "signal": None
    }
    result = statistical_alpha_filter(setup)
    assert not result[0]
    assert result[2].startswith("Rejected (")

def test_edge_case_boundary_input():
    setup = {
        "atr": 1000000000,
        "volume": np.inf,
        "taker_buy_ratio": 0.5,
        "rsi": 100,
        "signal": "LONG"
    }
    result = statistical_alpha_filter(setup)
    assert not result[0]
    assert result[2].startswith("Rejected (")

def test_error_case_invalid_input():
    setup = {
        "atr": "invalid",
        "volume": "invalid",
        "taker_buy_ratio": "invalid",
        "rsi": "invalid",
        "signal": "INVALID"
    }
    result = statistical_alpha_filter(setup)
    assert not result[0]
    assert result[2].startswith("Rejected (")