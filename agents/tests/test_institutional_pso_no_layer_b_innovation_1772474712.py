import numpy as np
from typing import List

def permutation_test_pf(oos_trades_r: List[float], n=500, seed=42) -> float:
    """
    Permute trade outcomes (signs) to estimate how often PF>=observed happens by chance.
    Returns p_value (smaller is better).
    """
    rng = np.random.default_rng(seed)
    arr = np.array(oos_trades_r, dtype=np.float32)
    if len(arr) < 20:
        return 1.0

    def pf_from_r(rvals: np.ndarray) -> float:
        wins = rvals[rvals > 0].sum()
        losses = np.abs(rvals[rvals < 0]).sum()
        return float(wins / losses) if losses > 0 else (99.0 if wins > 0 else 0.0)

    observed = pf_from_r(arr)
    count = 0
    for _ in range(n):
        signs = rng.choice([-1.0, 1.0], size=len(arr))
        perm = np.abs(arr) * signs
        if pf_from_r(perm) >= observed:
            count += 1
    return (count + 1) / (n + 1)

# Test code using pytest style
import pytest

def test_permutation_test_pf_happy_path():
    # Normal inputs
    oos_trades_r = [1.0, -2.0, 3.0, -4.0]
    result = permutation_test_pf(oos_trades_r)
    assert isinstance(result, float)
    assert 0 <= result <= 1

def test_permutation_test_pf_empty_input():
    # Edge case: empty input
    oos_trades_r = []
    result = permutation_test_pf(oos_trades_r)
    assert result == 1.0

def test_permutation_test_pf_single_positive_trade():
    # Edge case: single positive trade
    oos_trades_r = [1.0]
    result = permutation_test_pf(oos_trades_r)
    assert result == 1.0

def test_permutation_test_pf_single_negative_trade():
    # Edge case: single negative trade
    oos_trades_r = [-1.0]
    result = permutation_test_pf(oos_trades_r)
    assert result == 0.99

def test_permutation_test_pf_all_zeros():
    # Edge case: all zeros
    oos_trades_r = [0.0] * 20
    result = permutation_test_pf(oos_trades_r)
    assert result == 1.0

def test_permutation_test_pf_boundary_case():
    # Boundary case: exactly 20 trades
    oos_trades_r = [1.0] * 9 + [-1.0] * 11
    result = permutation_test_pf(oos_trades_r)
    assert isinstance(result, float)
    assert 0 <= result <= 1

def test_permutation_test_pf_invalid_input_type():
    # Error case: invalid input type (should not happen as inputs are already converted to np.float32)
    with pytest.raises(TypeError):
        permutation_test_pf('not a list')