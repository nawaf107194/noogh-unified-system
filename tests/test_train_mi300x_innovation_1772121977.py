import pytest

def score_length(text):
    words = len(text.split())
    if words < 10: return 0.1
    elif words < 30: return 0.4
    elif words < 100: return 0.7
    elif words < 500: return 1.0
    elif words < 1000: return 0.8
    return 0.5

def test_score_length_happy_path():
    assert score_length("This is a short text.") == 0.4
    assert score_length("A bit longer text, but still within the range.") == 0.7
    assert score_length("Another example with just under 100 words.") == 0.7
    assert score_length("A very long piece of text that should return 1.0") == 1.0

def test_score_length_edge_cases():
    assert score_length("") == 0.1
    assert score_length(None) is None
    assert score_length("Short") == 0.1
    assert score_length(" ".join(["a"] * 9)) == 0.1
    assert score_length(" ".join(["a"] * 30)) == 0.4
    assert score_length(" ".join(["a"] * 99)) == 0.7
    assert score_length(" ".join(["a"] * 500)) == 1.0
    assert score_length(" ".join(["a"] * 999)) == 0.8
    assert score_length("A text with exactly 100 words.") == 0.7

def test_score_length_error_cases():
    # The function does not explicitly raise any exceptions, so these tests are
    # more about ensuring it handles unexpected inputs gracefully.
    assert score_length(42) is None
    assert score_length([]) is None
    assert score_length({"key": "value"}) is None

def test_score_length_async_behavior():
    # This function does not perform any asynchronous operations, so there's
    # nothing to test in terms of async behavior.
    pass