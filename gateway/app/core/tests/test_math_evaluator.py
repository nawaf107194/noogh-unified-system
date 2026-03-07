import pytest
from gateway.app.core.math_evaluator import calculate_average

# Happy path (normal inputs)
def test_calculate_average_happy_path():
    assert calculate_average([1, 2, 3, 4, 5]) == (True, 3.0)
    assert calculate_average([10, 20, 30]) == (True, 20.0)

# Edge cases (empty, None, boundaries)
def test_calculate_average_empty_list():
    assert calculate_average([]) == (False, "لا توجد أرقام")

def test_calculate_average_single_element():
    assert calculate_average([42]) == (True, 42.0)

# Error cases (invalid inputs)
def test_calculate_average_with_non_numeric_values():
    with pytest.raises(TypeError):
        calculate_average(["a", "b", "c"])

def test_calculate_average_with_mixed_types():
    with pytest.raises(TypeError):
        calculate_average([1, "two", 3])

# Note: There is no async behavior in the provided function, so no async tests are needed.