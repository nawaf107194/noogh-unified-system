import pytest

from agents.inverse_arb_guide import InverseArbitrageGuide

@pytest.fixture
def guide():
    return InverseArbitrageGuide(capital=10000)

def test_calculate_position_happy_path(guide):
    """Test with normal inputs"""
    result = guide.calculate_position(price=50, funding_daily=-0.02, hold_days=14)
    assert result['capital'] == 10000
    assert result['position_coin'] == 200.0
    assert result['funding_collected'] == -280.0
    assert result['borrow_fees'] == 30.0
    assert result['trading_fees'] == 5.0
    assert result['total_fees'] == 35.0
    assert result['net_profit'] == -315.0
    assert result['roi_percent'] == -3.15
    assert result['apr_percent'] == -21.4286

def test_calculate_position_edge_cases(guide):
    """Test with edge cases"""
    # Edge case: hold_days = 1 (minimum)
    result = guide.calculate_position(price=50, funding_daily=-0.02, hold_days=1)
    assert result['capital'] == 10000
    assert result['position_coin'] == 200.0
    assert result['funding_collected'] == -2.0
    assert result['borrow_fees'] == 30.0
    assert result['trading_fees'] == 5.0
    assert result['total_fees'] == 37.0
    assert result['net_profit'] == -36.0
    assert result['roi_percent'] == -0.36
    assert result['apr_percent'] == -25.946

def test_calculate_position_error_cases(guide):
    """Test with error cases"""
    # Error case: negative price
    result = guide.calculate_position(price=-1, funding_daily=-0.02)
    assert result is None  # Assuming the function handles this gracefully

    # Error case: zero hold_days
    result = guide.calculate_position(price=50, funding_daily=-0.02, hold_days=0)
    assert result is None  # Assuming the function handles this gracefully

def test_calculate_position_async_behavior(guide):
    """Test with async behavior"""
    # This example does not show async behavior in the provided code
    pass