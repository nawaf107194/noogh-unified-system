import pytest
from typing import List

from gateway.app.ml.curriculum import get_all_domains, CURRICULUM

def test_get_all_domains_happy_path():
    """Test the happy path with normal inputs."""
    expected_domains = list(CURRICULUM.keys())
    assert get_all_domains() == expected_domains

def test_get_all_domains_empty_curriculum():
    """Test the edge case where the curriculum is empty."""
    CURRICULUM.clear()
    assert get_all_domains() == []

def test_get_all_domains_none_curriculum():
    """Test the edge case where the curriculum is None."""
    global CURRICULUM
    original_curriculum = CURRICULUM
    CURRICULUM = None
    with pytest.raises(TypeError):
        get_all_domains()
    CURRICULUM = original_curriculum

def test_get_all_domains_boundary_case():
    """Test boundary cases where the curriculum keys have boundaries."""
    # Assuming the curriculum keys have a specific structure, e.g., strings or numbers
    expected_domains = list(CURRICULUM.keys())
    assert get_all_domains() == expected_domains

# Note: There are no error cases in this function that explicitly raise exceptions,
# so there is no need to test for invalid inputs.