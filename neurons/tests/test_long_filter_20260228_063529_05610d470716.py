import pytest

def long_filter(s):
    atr = s.get('avg_atr', 0)
    vol_regime = s.get('volatility_regime', 'MEDIUM')
    if vol_regime == 'LOW' and atr < 0.005: return False, 0.0, 'Low ATR in Low Volatility'
    if vol_regime != 'LOW': return False, 0.0, 'Not Low Volatility'
    return True, min(1.0, atr / 0.05), 'ATR within range'

@pytest.mark.parametrize("input_data, expected_result", [
    ({"avg_atr": 0.003, "volatility_regime": "LOW"}, (False, 0.0, 'Low ATR in Low Volatility')),
    ({"avg_atr": 0.01, "volatility_regime": "MEDIUM"}, (False, 0.0, 'Not Low Volatility')),
    ({"avg_atr": 0.25, "volatility_regime": "LOW"}, (True, 5.0, 'ATR within range')),
    ({"avg_atr": 0.12, "volatility_regime": "HIGH"}, (False, 0.0, 'Not Low Volatility')),
    ({}, (False, 0.0, 'Not Low Volatility')),
    (None, (None, None, None)),
    ("not a dict", (None, None, None)),
    ({"avg_atr": "invalid", "volatility_regime": "LOW"}, (None, None, None)),
])
def test_long_filter(input_data, expected_result):
    result = long_filter(input_data)
    assert result == expected_result