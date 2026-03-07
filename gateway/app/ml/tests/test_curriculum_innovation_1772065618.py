import pytest

from src.gateway.app.ml.curriculum import get_curriculum, CURRICULUM

@pytest.mark.parametrize("domain, expected", [
    ("mathematics", {"course1": "algebra", "course2": "geometry"}),
    ("science", {"course1": "physics", "course2": "chemistry"}),
])
def test_get_curriculum_happy_path(domain, expected):
    """Test happy path where valid domain is provided."""
    result = get_curriculum(domain)
    assert result == expected

@pytest.mark.parametrize("domain, expected", [
    ("", {}),
    (None, {}),
    ("unknown_domain", {}),
])
def test_get_curriculum_edge_cases(domain, expected):
    """Test edge cases like empty string and None."""
    result = get_curriculum(domain)
    assert result == expected

@pytest.mark.parametrize("domain, expected", [
    ({}, "Invalid input type"),
    ([], "Invalid input type"),
    (123, "Invalid input type"),
])
def test_get_curriculum_error_cases(domain, expected):
    """Test error cases with invalid inputs."""
    with pytest.raises(TypeError) as exc_info:
        get_curriculum(domain)
    assert str(exc_info.value) == expected