import pytest

def test_check_health_happy_path():
    """Test the happy path where the health check returns True"""
    result = check_health()
    assert result is True