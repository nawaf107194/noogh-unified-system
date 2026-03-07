import pytest
from gateway.app.core.health import YourClass  # Replace with actual class name

def test_run_diagnostics_happy_path():
    # Setup
    instance = YourClass()
    
    # Execute
    result = instance.run_diagnostics()
    
    # Assert
    assert result == {"system": "healthy"}
    assert isinstance(result, dict)
    assert "system" in result
    assert result["system"] == "healthy"