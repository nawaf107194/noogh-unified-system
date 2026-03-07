import pytest

def test_calculate_dynamic_stop_loss_happy_path():
    # Normal inputs for LONG signal
    sl_price = calculate_dynamic_stop_loss(100, 'LONG', 85, 90)
    assert sl_price == 97.0
    
    # Normal inputs for SHORT signal
    sl_price = calculate_dynamic_stop_loss(100, 'SHORT', 35, 20)
    assert sl_price == 103.0

def test_calculate_dynamic_stop_loss_edge_cases():
    # Edge case: entry price at boundary values
    sl_price = calculate_dynamic_stop_loss(0.01, 'LONG', 85, 90)
    assert sl_price == pytest.approx(0.0097, reltol=1e-4)
    
    sl_price = calculate_dynamic_stop_loss(float('inf'), 'SHORT', 35, 20)
    assert sl_price == float('inf')
    
    # Edge case: empty string for signal_type
    sl_price = calculate_dynamic_stop_loss(100, '', 85, 90)
    assert sl_price == pytest.approx(97.0, reltol=1e-4)

def test_calculate_dynamic_stop_loss_error_cases():
    # Error case: invalid signal_type
    with pytest.raises(ValueError):
        calculate_dynamic_stop_loss(100, 'UNKNOWN', 85, 90)
    
    # Error case: negative liquidity_score
    sl_price = calculate_dynamic_stop_loss(100, 'LONG', -1, 90)
    assert sl_price == pytest.approx(97.0, reltol=1e-4)

def test_calculate_dynamic_stop_loss_boundary_cases():
    # Boundary case: base_sl_pct at boundary values
    sl_price = calculate_dynamic_stop_loss(100, 'LONG', 85, 90, 0)
    assert sl_price == pytest.approx(100.0, reltol=1e-4)
    
    sl_price = calculate_dynamic_stop_loss(100, 'SHORT', 35, 20, 100)
    assert sl_price == pytest.approx(100.0, reltol=1e-4)

def test_calculate_dynamic_stop_loss_low_liquidity_high_indicator():
    # Low liquidity but high indicator should yield minimal SL
    sl_price = calculate_dynamic_stop_loss(100, 'LONG', 35, 90)
    assert sl_price == pytest.approx(98.5, reltol=1e-4)
    
    sl_price = calculate_dynamic_stop_loss(100, 'SHORT', 65, 90)
    assert sl_price == pytest.approx(101.5, reltol=1e-4)

def test_calculate_dynamic_stop_loss_high_liquidity_low_indicator():
    # High liquidity but low indicator should yield minimal SL
    sl_price = calculate_dynamic_stop_loss(100, 'LONG', 90, 35)
    assert sl_price == pytest.approx(97.5, reltol=1e-4)
    
    sl_price = calculate_dynamic_stop_loss(100, 'SHORT', 90, 65)
    assert sl_price == pytest.approx(102.5, reltol=1e-4)