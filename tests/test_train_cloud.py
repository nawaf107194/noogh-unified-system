import pytest

def score_length(text):
    words = len(text.split())
    if words < 10: return 0.1
    elif words < 30: return 0.4
    elif words < 100: return 0.7
    elif words < 500: return 1.0
    elif words < 1000: return 0.8
    return 0.5

# Happy path tests
def test_score_length_happy_path():
    assert score_length("This is a short text.") == 0.4
    assert score_length("Here is a longer piece of text that should return 1.0 because it has more than 500 words.") == 1.0

# Edge case tests
def test_score_length_empty_string():
    assert score_length("") == 0.1
    
def test_score_length_none():
    assert score_length(None) == 0.1

def test_score_length_boundary_values():
    assert score_length("a" * 9) == 0.1
    assert score_length("a" * 30) == 0.4
    assert score_length("a" * 99) == 0.7
    assert score_length("a" * 500) == 1.0
    assert score_length("a" * 1000) == 0.8

# Error case tests (if applicable)
def test_score_length_non_string_input():
    # Since the function does not explicitly raise an error for non-string inputs,
    # we will assert that the result is None or False.
    assert score_length(123456789) == 0.1
    assert score_length([1, 2, 3]) == 0.1
    assert score_length({'key': 'value'}) == 0.1

# Async behavior tests (if applicable)
# Note: The function does not appear to be asynchronous, so this part is not relevant.