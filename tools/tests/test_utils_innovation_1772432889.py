import pytest

def safe_divide(a, b):
    if b == 0:
        return None
    else:
        return a / b

def test_serialization():
    # Happy path (normal inputs)
    assert safe_divide(10, 2) == 5
    
    # Edge cases (empty, None, boundaries)
    assert safe_divide(None, 2) is None
    assert safe_divide(10, None) is None
    assert safe_divide(0, 1) == 0
    assert safe_divide(-10, -2) == 5.0
    
    # Error cases (invalid inputs)
    # Since the function does not explicitly raise exceptions for invalid types,
    # we do not need to test for such cases.
    
    # Async behavior (if applicable)
    # The function is synchronous, so no async testing is needed.

pytest.main()