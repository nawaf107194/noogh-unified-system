import pytest
from gateway.app.analytics.insights_engine import get_insights_engine, InsightsEngine

# Mocking kpi_calculator for dependency injection
class MockKPICalculator:
    def calculate_kpis(self, data):
        return {}

def test_get_insights_engine_happy_path():
    # Arrange
    kpi_calculator = MockKPICalculator()
    
    # Act
    engine1 = get_insights_engine(kpi_calculator)
    engine2 = get_insights_engine(kpi_calculator)
    
    # Assert
    assert isinstance(engine1, InsightsEngine)
    assert engine1 is engine2  # Singleton check

def test_get_insights_engine_edge_cases():
    # Arrange
    kpi_calculator = None
    
    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        get_insights_engine(kpi_calculator)
    assert "AttributeError" in str(excinfo.value), "Expected AttributeError for None kpi_calculator"

def test_get_insights_engine_async_behavior():
    # Async behavior is not applicable here, so this test is a placeholder
    pass

# Additional tests can be added if more edge cases or error handling is identified