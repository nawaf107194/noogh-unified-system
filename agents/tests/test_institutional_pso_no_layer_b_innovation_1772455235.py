import pytest
from typing import List
import numpy as np
from agents.institutional_pso_no_layer_b import permutation_test_pf

def test_permutation_test_pf_happy_path():
    oos_trades_r = [1.0, -2.0, 3.0, -4.0, 5.0]
    p_value = permutation_test_pf(oos_trades_r)
    assert isinstance(p_value, float), "Output should be a float"
    assert 0 <= p_value <= 1, "P-value should be between 0 and 1"

def test_permutation_test_pf_empty_input():
    oos_trades_r: List[float] = []
    p_value = permutation_test_pf(oos_trades_r)
    assert p_value == 1.0, "Empty input should return 1.0"

def test_permutation_test_pf_none_input():
    with pytest.raises(TypeError):
        permutation_test_pf(None)

def test_permutation_test_pf_single_positive_trade():
    oos_trades_r = [1.0]
    p_value = permutation_test_pf(oos_trades_r)
    assert p_value == 1.0, "Single positive trade should return 1.0"

def test_permutation_test_pf_single_negative_trade():
    oos_trades_r = [-1.0]
    p_value = permutation_test_pf(oos_trades_r)
    assert p_value == 1.0, "Single negative trade should return 1.0"

def test_permutation_test_pf_boundary_values():
    oos_trades_r = [1e-38] * 20
    p_value = permutation_test_pf(oos_trades_r)
    assert p_value == 1.0, "Boundary values should return 1.0"