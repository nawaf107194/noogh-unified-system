import pytest
from typing import List, Dict

@pytest.fixture
def valid_setups():
    return [
        {'signal': 'LONG', 'outcome': 'WIN'},
        {'signal': 'LONG', 'outcome': 'LOSS'},
        {'signal': 'SHORT', 'outcome': 'WIN'},
        {'signal': 'SHORT', 'outcome': 'LOSS'},
        {'signal': 'LONG', 'outcome': 'WIN'},
    ]

def test_calculate_current_performance_happy_path(valid_setups):
    result = calculate_current_performance(valid_setups)
    assert result == {
        'total_setups': 5,
        'long': {'wins': 2, 'losses': 1},
        'short': {'wins': 1, 'losses': 1}
    }

def test_calculate_current_performance_empty_input():
    result = calculate_current_performance([])
    assert result == {
        'total_setups': 0,
        'long': {'wins': 0, 'losses': 0},
        'short': {'wins': 0, 'losses': 0}
    }

def test_calculate_current_performance_all_wins():
    setups = [
        {'signal': 'LONG', 'outcome': 'WIN'},
        {'signal': 'SHORT', 'outcome': 'WIN'},
        {'signal': 'LONG', 'outcome': 'WIN'},
    ]
    result = calculate_current_performance(setups)
    assert result == {
        'total_setups': 3,
        'long': {'wins': 2, 'losses': 0},
        'short': {'wins': 1, 'losses': 0}
    }

def test_calculate_current_performance_invalid_input():
    # Test with invalid input type
    result = calculate_current_performance(None)
    assert result is None
    
    # Test with invalid setup structure
    result = calculate_current_performance([{}])
    assert result == {
        'total_setups': 1,
        'long': {'wins': 0, 'losses': 0},
        'short': {'wins': 0, 'losses': 0}
    }

def test_calculate_current_performance_single_setup():
    setup = [{'signal': 'SHORT', 'outcome': 'LOSS'}]
    result = calculate_current_performance(setup)
    assert result == {
        'total_setups': 1,
        'long': {'wins': 0, 'losses': 0},
        'short': {'wins': 0, 'losses': 1}
    }

def test_calculate_current_performance_unknown_signal():
    setups = [
        {'signal': 'UNKNOWN', 'outcome': 'WIN'},
        {'signal': 'LONG', 'outcome': 'UNKNOWN'},
    ]
    result = calculate_current_performance(setups)
    assert result == {
        'total_setups': 2,
        'long': {'wins': 0, 'losses': 0},
        'short': {'wins': 0, 'losses': 0}
    }