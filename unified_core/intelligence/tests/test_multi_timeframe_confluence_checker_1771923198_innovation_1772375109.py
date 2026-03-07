import pytest

from unified_core.intelligence.multi_timeframe_confluence_checker_1771923198 import MultiTimeframeConfluenceChecker

def test_evaluate_confluence_happy_path():
    checker = MultiTimeframeConfluenceChecker()
    confluence_data = {
        'timeframe1': {'RSI': 50, 'MACD': -30},
        'timeframe2': {'RSI': 60, 'MACD': -70}
    }
    result = checker.evaluate_confluence(confluence_data)
    assert result is True

def test_evaluate_confluence_edge_case_empty():
    checker = MultiTimeframeConfluenceChecker()
    confluence_data = {}
    result = checker.evaluate_confluence(confluence_data)
    assert result is False

def test_evaluate_confluence_edge_case_none():
    checker = MultiTimeframeConfluenceChecker()
    confluence_data = None
    result = checker.evaluate_confluence(confluence_data)
    assert result is False

def test_evaluate_confluence_boundary_rsi_too_low():
    checker = MultiTimeframeConfluenceChecker()
    confluence_data = {
        'timeframe1': {'RSI': 0, 'MACD': -30}
    }
    result = checker.evaluate_confluence(confluence_data)
    assert result is False

def test_evaluate_confluence_boundary_rsi_too_high():
    checker = MultiTimeframeConfluenceChecker()
    confluence_data = {
        'timeframe1': {'RSI': 70, 'MACD': -30}
    }
    result = checker.evaluate_confluence(confluence_data)
    assert result is False

def test_evaluate_confluence_boundary_macd_too_high():
    checker = MultiTimeframeConfluenceChecker()
    confluence_data = {
        'timeframe1': {'RSI': 50, 'MACD': -200}
    }
    result = checker.evaluate_confluence(confluence_data)
    assert result is False

def test_evaluate_confluence_boundary_macd_too_low():
    checker = MultiTimeframeConfluenceChecker()
    confluence_data = {
        'timeframe1': {'RSI': 50, 'MACD': -50}
    }
    result = checker.evaluate_confluence(confluence_data)
    assert result is False