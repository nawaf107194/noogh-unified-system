import pytest

from agents.funding_scanner_v2 import FundingScannerV2, calculate_arb_metrics

def test_happy_path():
    scanner = FundingScannerV2()
    result = scanner.calculate_arb_metrics('BTCUSD', 0.5, exchange='bybit')
    assert isinstance(result, dict)
    assert result['symbol'] == 'BTCUSD'
    assert result['avg_funding_8h'] == 0.5
    assert result['hold_days'] == 14
    assert result['total_funding'] > 0
    assert result['net_return'] > 0
    assert result['annualized_apr'] > 0
    assert result['profitable']

def test_edge_case_symbol_none():
    scanner = FundingScannerV2()
    result = scanner.calculate_arb_metrics(None, 0.5, exchange='bybit')
    assert isinstance(result, dict)
    assert result['symbol'] is None

def test_edge_case_avg_funding_rate_zero():
    scanner = FundingScannerV2()
    result = scanner.calculate_arb_metrics('BTCUSD', 0.0, exchange='bybit')
    assert isinstance(result, dict)
    assert result['total_funding'] == 0
    assert result['net_return'] == 0

def test_edge_case_hold_days_min():
    scanner = FundingScannerV2()
    result = scanner.calculate_arb_metrics('BTCUSD', 0.5, hold_days=1, exchange='bybit')
    assert isinstance(result, dict)
    assert result['total_funding'] > 0
    assert result['net_return'] > 0

def test_edge_case_hold_days_max():
    scanner = FundingScannerV2()
    result = scanner.calculate_arb_metrics('BTCUSD', 0.5, hold_days=30, exchange='bybit')
    assert isinstance(result, dict)
    assert result['total_funding'] > 0
    assert result['net_return'] > 0

def test_edge_case_exchange_not_found():
    scanner = FundingScannerV2()
    result = scanner.calculate_arb_metrics('BTCUSD', 0.5, exchange='unknown')
    assert isinstance(result, dict)
    assert result['exchange'] == 'bybit'

def test_error_case_symbol_invalid_type():
    scanner = FundingScannerV2()
    with pytest.raises(TypeError):
        scanner.calculate_arb_metrics(123, 0.5, exchange='bybit')

def test_error_case_avg_funding_rate_negative():
    scanner = FundingScannerV2()
    with pytest.raises(ValueError):
        scanner.calculate_arb_metrics('BTCUSD', -0.1, exchange='bybit')