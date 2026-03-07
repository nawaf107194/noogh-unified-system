import pytest
from your_module import calculate_indicators  # Adjust the import accordingly

def test_happy_path():
    data = {
        'close': [10, 20, 30, 40, 50],
        'high': [12, 22, 32, 42, 52],
        'low': [8, 18, 28, 38, 48]
    }
    rsi, atr = calculate_indicators(data)
    assert len(rsi) == len(data['close'])
    assert len(atr) == len(data['close'])

def test_empty_data():
    data = {
        'close': [],
        'high': [],
        'low': []
    }
    rsi, atr = calculate_indicators(data)
    assert len(rsi) == 0
    assert len(atr) == 0

def test_none_input():
    with pytest.raises(TypeError):
        calculate_indicators(None)

def test_boundary_inputs():
    data = {
        'close': [10],
        'high': [12],
        'low': [8]
    }
    rsi, atr = calculate_indicators(data)
    assert len(rsi) == 1
    assert len(atr) == 1

def test_invalid_inputs():
    with pytest.raises(ValueError):
        data = {
            'close': [10, 20, 30],
            'high': [12, 22, None],  # Invalid input: None value in high
            'low': [8, 18, 28]
        }
        calculate_indicators(data)