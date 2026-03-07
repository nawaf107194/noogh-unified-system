import pytest

def long_filter(s):
    atr = s.get('avg_atr', 0)
    vol_regime = s.get('volatility_regime', 'MEDIUM')
    if vol_regime == 'LOW' and atr < 0.005: return False, 0.0, 'Low ATR in Low Volatility'
    if vol_regime != 'LOW': return False, 0.0, 'Not Low Volatility'
    return True, min(1.0, atr / 0.05), 'ATR within range'

@pytest.mark.parametrize("input_data, expected_output", [
    ({"avg_atr": 0.006, "volatility_regime": "MEDIUM"}, (True, 12.0, 'ATR within range')),
    ({"avg_atr": 0.004, "volatility_regime": "LOW"}, (False, 0.0, 'Low ATR in Low Volatility')),
    ({"avg_atr": 0.005, "volatility_regime": "MEDIUM"}, (False, 0.0, 'Not Low Volatility')),
    ({"avg_atr": None, "volatility_regime": "LOW"}, (True, 0.0, 'ATR within range')),
    ({"avg_atr": 0.006, "volatility_regime": None}, (False, 0.0, 'Not Low Volatility')),
    ({}, (False, 0.0, 'Not Low Volatility')),
    (None, (False, 0.0, 'Not Low Volatility')),
    ([], (False, 0.0, 'Not Low Volatility')),
    ("string", (False, 0.0, 'Not Low Volatility'))
])
def test_long_filter(input_data, expected_output):
    assert long_filter(input_data) == expected_output