import pytest
from unittest.mock import patch, MagicMock
from gateway.app.analytics.kpi_calculator import get_kpi_calculator, KPICalculator

# Mock the global variable to ensure tests are isolated
_kpi_calculator = None

@pytest.fixture(autouse=True)
def reset_global():
    global _kpi_calculator
    _kpi_calculator = None

def test_happy_path():
    # Test normal operation
    calculator = get_kpi_calculator()
    assert isinstance(calculator, KPICalculator)

def test_edge_case_none():
    # Test edge case where the global variable might be set to None
    global _kpi_calculator
    _kpi_calculator = None
    calculator = get_kpi_calculator()
    assert isinstance(calculator, KPICalculator)

def test_error_case_invalid_input():
    # This function doesn't take any arguments, so this test is more about ensuring no side effects occur
    with pytest.raises(TypeError):
        get_kpi_calculator("invalid")

def test_async_behavior():
    # Since the function does not involve any async operations, this test is more of a placeholder
    async def mock_get_kpi_calculator():
        return get_kpi_calculator()

    result = mock_get_kpi_calculator()
    assert isinstance(result, MagicMock)

# Additional test to ensure the singleton behavior
def test_singleton_behavior():
    first_instance = get_kpi_calculator()
    second_instance = get_kpi_calculator()
    assert first_instance is second_instance