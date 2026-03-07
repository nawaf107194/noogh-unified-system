import pytest

from unified_core.intelligence.volatility_adjusted_position_sizing import VolatilityAdjustedPositionSizing

def test_init_happy_path():
    sizing = VolatilityAdjustedPositionSizing(base_leverage=20, max_leverage=50, min_leverage=5)
    assert sizing.base_leverage == 20
    assert sizing.max_leverage == 50
    assert sizing.min_leverage == 5

def test_init_edge_case_empty_values():
    sizing = VolatilityAdjustedPositionSizing(base_leverage=None, max_leverage=None, min_leverage=None)
    assert sizing.base_leverage is None
    assert sizing.max_leverage is None
    assert sizing.min_leverage is None

def test_init_edge_case_boundaries():
    sizing = VolatilityAdjustedPositionSizing(base_leverage=5, max_leverage=20, min_leverage=1)
    assert sizing.base_leverage == 5
    assert sizing.max_leverage == 20
    assert sizing.min_leverage == 1

def test_init_error_case_invalid_input():
    with pytest.raises(ValueError):
        VolatilityAdjustedPositionSizing(base_leverage=-10, max_leverage=50, min_leverage=5)