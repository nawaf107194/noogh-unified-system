import pytest

from unified_core.observability.health import Health


def test_init_happy_path():
    """Test initialization with valid service_name."""
    health_checker = Health(service_name="my_service")
    assert health_checker.service_name == "my_service"
    assert isinstance(health_checker._readiness_checks, dict)
    assert isinstance(health_checker._component_status, dict)


def test_init_edge_case_empty_string():
    """Test initialization with an empty string as service_name."""
    health_checker = Health(service_name="")
    assert health_checker.service_name == ""
    assert isinstance(health_checker._readiness_checks, dict)
    assert isinstance(health_checker._component_status, dict)


def test_init_edge_case_none():
    """Test initialization with None as service_name."""
    health_checker = Health(service_name=None)
    assert health_checker.service_name is None
    assert isinstance(health_checker._readiness_checks, dict)
    assert isinstance(health_checker._component_status, dict)


def test_init_error_case_invalid_input_type():
    """Test that no exception is raised for invalid input type."""
    health_checker = Health(service_name=12345)
    assert isinstance(health_checker.service_name, str)
    assert health_checker.service_name == "12345"
    assert isinstance(health_checker._readiness_checks, dict)
    assert isinstance(health_checker._component_status, dict)