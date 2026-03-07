import pytest
from unittest.mock import patch, MagicMock
import time

class TestResilienceExecute:
    @pytest.fixture
    def resilience_instance(self):
        from gateway.app.core.resilience import Resilience
        return Resilience(reset_timeout=1)

    def test_happy_path(self, resilience_instance):
        # Arrange
        operation = MagicMock(return_value="Success")
        resilience_instance.state = CircuitState.CLOSED

        # Act
        result = resilience_instance.execute(operation, arg1="arg1", kwarg1="kwarg1")

        # Assert
        assert result == "Success"
        operation.assert_called_once_with(arg1="arg1", kwarg1="kwarg1")
        assert resilience_instance.state == CircuitState.CLOSED

    def test_circuit_open_and_reset_timeout(self, resilience_instance):
        # Arrange
        operation = MagicMock(return_value="Success")
        resilience_instance.state = CircuitState.OPEN
        resilience_instance.last_failure_time = time.time() - 2
        resilience_instance.reset_timeout = 1

        # Act
        result = resilience_instance.execute(operation, arg1="arg1", kwarg1="kwarg1")

        # Assert
        assert result == "Success"
        operation.assert_called_once_with(arg1="arg1", kwarg1="kwarg1")
        assert resilience_instance.state == CircuitState.CLOSED

    def test_circuit_open_and_no_reset_timeout(self, resilience_instance):
        # Arrange
        operation = MagicMock(side_effect=ValueError("Expected Error"))
        resilience_instance.state = CircuitState.OPEN
        resilience_instance.last_failure_time = time.time() - 0.5
        resilience_instance.reset_timeout = 1

        with pytest.raises(ValueError) as exc_info:
            resilience_instance.execute(operation, arg1="arg1", kwarg1="kwarg1")

        # Assert
        assert str(exc_info.value) == "Expected Error"
        operation.assert_called_once_with(arg1="arg1", kwarg1="kwarg1")
        assert resilience_instance.state == CircuitState.OPEN

    def test_circuit_half_open(self, resilience_instance):
        # Arrange
        operation = MagicMock(return_value="Success")
        resilience_instance.state = CircuitState.HALF_OPEN
        resilience_instance.last_failure_time = time.time() - 2
        resilience_instance.reset_timeout = 1

        # Act
        result = resilience_instance.execute(operation, arg1="arg1", kwarg1="kwarg1")

        # Assert
        assert result == "Success"
        operation.assert_called_once_with(arg1="arg1", kwarg1="kwarg1")
        assert resilience_instance.state == CircuitState.CLOSED

    def test_circuit_half_open_failure(self, resilience_instance):
        # Arrange
        operation = MagicMock(side_effect=ValueError("Expected Error"))
        resilience_instance.state = CircuitState.HALF_OPEN
        resilience_instance.last_failure_time = time.time() - 2
        resilience_instance.reset_timeout = 1

        with pytest.raises(ValueError) as exc_info:
            resilience_instance.execute(operation, arg1="arg1", kwarg1="kwarg1")

        # Assert
        assert str(exc_info.value) == "Expected Error"
        operation.assert_called_once_with(arg1="arg1", kwarg1="kwarg1")
        assert resilience_instance.state == CircuitState.OPEN

    def test_handle_failure(self, resilience_instance):
        # Arrange
        operation = MagicMock(side_effect=ValueError("Expected Error"))
        resilience_instance.state = CircuitState.CLOSED
        resilience_instance.last_failure_time = time.time()
        resilience_instance.reset_timeout = 1
        resilience_instance.failure_count = 5

        with pytest.raises(ValueError) as exc_info:
            resilience_instance.execute(operation, arg1="arg1", kwarg1="kwarg1")

        # Assert
        assert str(exc_info.value) == "Expected Error"
        operation.assert_called_once_with(arg1="arg1", kwarg1="kwarg1")
        assert resilience_instance.state == CircuitState.OPEN
        assert resilience_instance.failure_count == 6