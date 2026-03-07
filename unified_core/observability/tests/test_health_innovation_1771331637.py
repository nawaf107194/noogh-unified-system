import pytest
from unittest.mock import Mock

class HealthChecker:
    def __init__(self):
        self._readiness_checks = {}
        self.logger = Mock()

    def register_readiness_check(self, component: str, check_fn: callable):
        """
        Register a readiness check for a component.
        
        Args:
            component: Component name (redis, agents, registry, etc.)
            check_fn: Function that returns True if component is ready
        """
        self._readiness_checks[component] = check_fn
        self.logger.info(f"Registered readiness check: {component}")

@pytest.fixture
def health_checker():
    return HealthChecker()

def test_register_readiness_check_happy_path(health_checker):
    # Arrange
    component_name = "test_component"
    check_function = lambda: True

    # Act
    health_checker.register_readiness_check(component_name, check_function)

    # Assert
    assert component_name in health_checker._readiness_checks
    assert health_checker._readiness_checks[component_name]() == True
    health_checker.logger.info.assert_called_with(f"Registered readiness check: {component_name}")

def test_register_readiness_check_empty_string(health_checker):
    # Arrange
    component_name = ""
    check_function = lambda: True

    # Act & Assert
    with pytest.raises(ValueError, match="Component name cannot be empty"):
        health_checker.register_readiness_check(component_name, check_function)

def test_register_readiness_check_none_component(health_checker):
    # Arrange
    component_name = None
    check_function = lambda: True

    # Act & Assert
    with pytest.raises(TypeError, match="NoneType.*missing 1 required positional argument: 'component'"):
        health_checker.register_readiness_check(component_name, check_function)

def test_register_readiness_check_none_check_fn(health_checker):
    # Arrange
    component_name = "test_component"

    # Act & Assert
    with pytest.raises(TypeError, match="missing 1 required positional argument: 'check_fn'"):
        health_checker.register_readiness_check(component_name, None)

def test_register_readiness_check_invalid_check_fn(health_checker):
    # Arrange
    component_name = "test_component"
    check_function = "not a function"

    # Act & Assert
    with pytest.raises(TypeError, match=".*is not callable"):
        health_checker.register_readiness_check(component_name, check_function)

def test_register_readiness_check_duplicate_registration(health_checker):
    # Arrange
    component_name = "test_component"
    check_function = lambda: True

    # Act
    health_checker.register_readiness_check(component_name, check_function)
    new_check_function = lambda: False

    # Assert
    with pytest.raises(KeyError, match=f"Component '{component_name}' already has a registered check."):
        health_checker.register_readiness_check(component_name, new_check_function)