import pytest

from unified_core.intelligence.hedging_mechanism_module import HedgingMechanismModule

def test_hedging_mechanism_module_happy_path():
    # Test with normal input
    hedger = HedgingMechanismModule(max_hedge_ratio=0.5)
    assert hedger.max_hedge_ratio == 0.5

def test_hedging_mechanism_module_edge_case_max_hedge_ratio_zero():
    # Edge case: max_hedge_ratio is zero
    hedger = HedgingMechanismModule(max_hedge_ratio=0.0)
    assert hedger.max_hedge_ratio == 0.0

def test_hedging_mechanism_module_edge_case_max_hedge_ratio_one():
    # Edge case: max_hedge_ratio is one
    hedger = HedgingMechanismModule(max_hedge_ratio=1.0)
    assert hedger.max_hedge_ratio == 1.0

def test_hedging_mechanism_module_error_case_negative_max_hedge_ratio():
    # Error case: negative max_hedge_ratio
    with pytest.raises(ValueError):
        HedgingMechanismModule(max_hedge_ratio=-0.1)

def test_hedging_mechanism_module_error_case_non_numeric_max_hedge_ratio():
    # Error case: non-numeric max_hedge_ratio
    with pytest.raises(TypeError):
        HedgingMechanismModule(max_hedge_ratio="not_a_number")