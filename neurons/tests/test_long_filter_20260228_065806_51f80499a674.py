import pytest

def long_filter(s):
    atr = s.get('atr', 0)
    tbr = s.get('taker_buy_ratio', 0)
    if atr < 5 or tbr < 0.5:
        return False, 0.0, 'ATR too low or TBR below threshold'
    return True, min(1.0, atr / 100), 'Long conditions met'

@pytest.mark.parametrize("test_input, expected", [
    ({"atr": 6, "taker_buy_ratio": 0.7}, (True, 0.06, 'Long conditions met')),
    ({"atr": 4, "taker_buy_ratio": 0.5}, (False, 0.0, 'ATR too low or TBR below threshold')),
    ({"atr": 10, "taker_buy_ratio": 4}, (True, 0.1, 'Long conditions met')),
])
def test_long_filter_happy_path(test_input, expected):
    assert long_filter(test_input) == expected

@pytest.mark.parametrize("test_input", [
    {},
    None,
    {"atr": None, "taker_buy_ratio": None},
    {"atr": 5, "taker_buy_ratio": -0.1},
    {"atr": -5, "taker_buy_ratio": 0.6},
])
def test_long_filter_edge_cases(test_input):
    result = long_filter(test_input)
    assert not result[0]
    assert result[1] == 0.0
    assert result[2].startswith('ATR too low or TBR below threshold')

@pytest.mark.parametrize("test_input", [
    "not a dictionary",
    {"atr": "not a number", "taker_buy_ratio": 0.5},
    {"atr": 1, "taker_buy_ratio": "not a number"},
])
def test_long_filter_error_cases(test_input):
    result = long_filter(test_input)
    assert result[0] is False
    assert result[1] == 0.0
    assert result[2].startswith('ATR too low or TBR below threshold')