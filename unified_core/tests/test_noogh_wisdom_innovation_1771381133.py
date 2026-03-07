import pytest
from typing import List
from noogh_wisdom import volume_profile

@pytest.mark.parametrize("volumes, expected", [
    ([1.0] * 30, "NORMAL"),  # Normal input with all volumes equal
    ([1.0] * 25 + [2.0] * 5, "HIGH"),  # Recent volumes higher than average
    ([1.0] * 25 + [0.5] * 5, "LOW"),  # Recent volumes lower than average
    ([1.0] * 25 + [3.0] * 5, "SPIKE"),  # Recent volumes much higher than average
])
def test_volume_profile_happy_path(volumes: List[float], expected: str):
    assert volume_profile(volumes) == expected

@pytest.mark.parametrize("volumes, expected", [
    ([], "NORMAL"),  # Empty list
    ([1.0] * 9, "NORMAL"),  # Less than 10 elements
    ([1.0] * 10, "NORMAL"),  # Exactly 10 elements
])
def test_volume_profile_edge_cases(volumes: List[float], expected: str):
    assert volume_profile(volumes) == expected

@pytest.mark.parametrize("volumes", [
    ("not a list"),  # Invalid input type
    ([1.0, "not a float"]),  # List with invalid element type
])
def test_volume_profile_error_cases(volumes):
    with pytest.raises(TypeError):
        volume_profile(volumes)

# Since the function is synchronous and does not involve any async behavior,
# there's no need to test for async behavior.