import pytest

from agents.runpod_neuron_generator import calculate_current_performance

def test_calculate_current_performance_happy_path():
    setups = [
        {'signal': 'LONG', 'outcome': 'WIN'},
        {'signal': 'LONG', 'outcome': 'LOSS'},
        {'signal': 'SHORT', 'outcome': 'WIN'},
        {'signal': 'SHORT', 'outcome': 'LOSS'}
    ]
    result = calculate_current_performance(setups)
    assert result == {
        'total_setups': 4,
        'long': {'wins': 1, 'losses': 1},
        'short': {'wins': 1, 'losses': 1}
    }

def test_calculate_current_performance_empty_input():
    setups = []
    result = calculate_current_performance(setups)
    assert result == {
        'total_setups': 0,
        'long': {'wins': 0, 'losses': 0},
        'short': {'wins': 0, 'losses': 0}
    }

def test_calculate_current_performance_none_input():
    setups = None
    result = calculate_current_performance(setups)
    assert result is None

def test_calculate_current_performance_invalid_signal():
    setups = [
        {'signal': 'LONG', 'outcome': 'WIN'},
        {'signal': 'LONG', 'outcome': 'LOSS'},
        {'signal': 'SHORT', 'outcome': 'WIN'},
        {'signal': 'INVALID', 'outcome': 'LOSS'}
    ]
    result = calculate_current_performance(setups)
    assert result == {
        'total_setups': 4,
        'long': {'wins': 1, 'losses': 1},
        'short': {'wins': 1, 'losses': 0}
    }

def test_calculate_current_performance_invalid_outcome():
    setups = [
        {'signal': 'LONG', 'outcome': 'WIN'},
        {'signal': 'LONG', 'outcome': 'LOSS'},
        {'signal': 'SHORT', 'outcome': 'INVALID'},
        {'signal': 'SHORT', 'outcome': 'LOSS'}
    ]
    result = calculate_current_performance(setups)
    assert result == {
        'total_setups': 4,
        'long': {'wins': 1, 'losses': 1},
        'short': {'wins': 0, 'losses': 1}
    }

def test_calculate_current_performance_mixed_invalid():
    setups = [
        {'signal': 'LONG', 'outcome': 'WIN'},
        {'signal': 'INVALID', 'outcome': 'LOSS'},
        {'signal': 'SHORT', 'outcome': 'INVALID'},
        {'signal': 'SHORT', 'outcome': 'LOSS'}
    ]
    result = calculate_current_performance(setups)
    assert result == {
        'total_setups': 4,
        'long': {'wins': 1, 'losses': 0},
        'short': {'wins': 0, 'losses': 1}
    }