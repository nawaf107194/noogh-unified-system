import pytest

from gateway.app.health_check import check_health

def test_check_health_happy_path():
    result = check_health()
    assert result is True, "Expected health check to return True for happy path"

def test_check_health_edge_cases():
    with pytest.raises(NotImplementedError):
        # Assuming the function should raise NotImplementedError if called directly
        check_health(None)