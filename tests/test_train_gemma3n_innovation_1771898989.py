import pytest

def score_length(text: str) -> float:
    """كافأة الطول المناسب"""
    words = len(text.split())
    
    if words < 10:
        return 0.1   # Too short
    elif words < 30:
        return 0.4   # Brief
    elif words < 100:
        return 0.7   # Good
    elif words < 500:
        return 1.0   # Detailed
    elif words < 1000:
        return 0.8   # Long but ok
    else:
        return 0.5   # Too long (may be padded)

@pytest.mark.parametrize("text, expected", [
    ("Hello world", 0.4),         # Brief
    ("This is a longer sentence with more than ten words.", 0.7),  # Good
    ("A bit longer than good but not too detailed.", 0.8),  # Long but ok
    ("Short", 0.1),               # Too short
    ("Just in the boundary of brief and good", 0.4),  # Brief boundary
    ("Right at the boundary of good and detailed", 0.7),  # Good boundary
    ("Exactly at the 500 word mark.", 1.0),  # Detailed
    ("Very very long sentence that exceeds one thousand words for sure.", 0.8),  # Long but ok
    ("One thousand words or more, this is too long.", 0.5),  # Too long
])
def test_score_length_happy_path(text: str, expected: float):
    assert score_length(text) == expected

@pytest.mark.parametrize("text", [
    "",                      # Empty string
    None,                    # None input
])
def test_score_length_edge_cases(text: str):
    assert score_length(text) is None  # Assuming it returns None for invalid inputs

# Error cases are not applicable here as the function does not explicitly raise exceptions