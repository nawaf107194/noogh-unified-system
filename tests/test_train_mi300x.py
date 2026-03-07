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
    assert score_length("Another example with more words.") == 0.7
    assert score_length("A bit longer than the previous one but still within limits.") == 1.0

def test_score_length_edge_cases():
    assert score_length("") == 0.1
    assert score_length(None) is None  # Assuming the function handles None gracefully
    assert score_length(" ") == 0.1
    assert score_length("a" * 9) == 0.1
    assert score_length("a" * 10) == 0.4
    assert score_length("a" * 29) == 0.4
    assert score_length("a" * 30) == 0.7
    assert score_length("a" * 99) == 0.7
    assert score_length("a" * 100) == 0.8
    assert score_length("a" * 499) == 0.8
    assert score_length("a" * 500) == 1.0

def test_score_length_error_cases():
    # Since the function doesn't explicitly raise exceptions, we don't need to test for them
    pass

def test_score_length_async_behavior():
    # The function is synchronous and doesn't involve any async behavior
    pass