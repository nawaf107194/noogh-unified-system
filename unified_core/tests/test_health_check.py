import pytest

from unified_core.health_check import HealthCheck

@pytest.fixture
def health_check_instance():
    return HealthCheck()

def test_get_health_status_happy_path(health_check_instance):
    # Arrange
    health_check_instance.metrics = {
        "cpu": 50,
        "memory": 75
    }
    
    # Act
    result = health_check_instance.get_health_status()
    
    # Assert
    assert isinstance(result, dict)
    assert len(result) == 2
    assert result["cpu"] == 50
    assert result["memory"] == 75

def test_get_health_status_empty_metrics(health_check_instance):
    # Arrange
    health_check_instance.metrics = {}
    
    # Act
    result = health_check_instance.get_health_status()
    
    # Assert
    assert isinstance(result, dict)
    assert len(result) == 0

def test_get_health_status_none_metrics(health_check_instance):
    # Arrange
    health_check_instance.metrics = None
    
    # Act
    result = health_check_instance.get_health_status()
    
    # Assert
    assert result is None