import pytest

from neural_engine.react_loop import evaluate


def test_happy_path():
    assert evaluate("3 + 5") == 8
    assert evaluate("2 * 3") == 6
    assert evaluate("10 / 2") == 5.0
    assert evaluate("2 ** 3") == 8
    assert evaluate("(1 + 2) * (3 - 4)") == -2


def test_edge_cases():
    assert evaluate("") is None
    assert evaluate(None) is None
    assert evaluate(" ") is None
    assert evaluate("1000000000000000") == 1000000000000000


def test_invalid_inputs():
    assert evaluate("3 + a") is None
    assert evaluate("5 / 0") is None
    assert evaluate("sqrt(-4)") is None
    assert evaluate("123abc") is None


def test_complex_expression():
    assert evaluate("(2 + sqrt(9)) * (4 - 3)") == 8.0


def test_invalid_characters():
    assert evaluate("5+3,,") == 8
    assert evaluate("5?3?") == 8
    assert evaluate("5*3x") == 15


def test_sqrt_symbol():
    assert evaluate("√4") == 2
    assert evaluate("sqrt(16)") == 4