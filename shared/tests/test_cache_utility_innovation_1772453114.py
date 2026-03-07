import pytest

def expensive_function(x, y):
    print("Executing expensive function...")
    return x * y

# Happy path (normal inputs)
def test_expensive_function_happy_path():
    assert expensive_function(2, 3) == 6
    assert expensive_function(-1, -1) == 1
    assert expensive_function(0, 5) == 0
    assert expensive_function(4.5, 2) == 9.0

# Edge cases (empty, None, boundaries)
def test_expensive_function_edge_cases():
    assert expensive_function(None, None) is None
    assert expensive_function("", "") is None
    assert expensive_function(1, float('inf')) is None
    assert expensive_function(float('-inf'), 1) is None

# Error cases (invalid inputs) - This function does not raise exceptions explicitly
# If the function were to raise exceptions for invalid inputs, these tests would be added here
# For example:
# def test_expensive_function_invalid_inputs():
#     with pytest.raises(ValueError):
#         expensive_function("a", "b")
#     with pytest.raises(TypeError):
#         expensive_function([1, 2], [3, 4])

# Async behavior (not applicable as the function is synchronous)