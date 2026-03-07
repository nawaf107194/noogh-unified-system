import pytest

from unified_core.core.asaa import ASAA


@pytest.fixture
def asaa_instance():
    return ASAA()


def test_calculate_friction_happy_path(asaa_instance):
    # Happy path with normal inputs
    result = asaa_instance._calculate_friction(fragility=0.5, impact=3)
    assert result == 7.5, "Expected friction to be 7.5 for fragility 0.5 and impact 3"

def test_calculate_friction_edge_case_fragility_zero(asaa_instance):
    # Edge case: fragility is zero
    result = asaa_instance._calculate_friction(fragility=0.0, impact=1)
    assert result == 2.0, "Expected friction to be 2.0 for fragility 0.0 and impact 1"

def test_calculate_friction_edge_case_impact_threshold(asaa_instance):
    # Edge case: impact is at the high threshold
    result = asaa_instance._calculate_friction(fragility=0.3, impact=asaa_instance.IMPACT_HIGH_THRESHOLD)
    assert result == 4.5, "Expected friction to be 4.5 for fragility 0.3 and impact at high threshold"

def test_calculate_friction_edge_case_max_friction(asaa_instance):
    # Edge case: maximum friction is reached
    result = asaa_instance._calculate_friction(fragility=1.0, impact=1)
    assert result == 2.0, "Expected friction to be max(2.0, min(4.0))"

def test_calculate_friction_error_case_invalid_fragility(asaa_instance):
    # Error case: invalid fragility (should not happen in this function, but testing for completeness)
    with pytest.raises(TypeError):
        asaa_instance._calculate_friction(fragility=None, impact=1)

def test_calculate_friction_error_case_invalid_impact(asaa_instance):
    # Error case: invalid impact (should not happen in this function, but testing for completeness)
    with pytest.raises(TypeError):
        asaa_instance._calculate_friction(fragility=0.5, impact="high")