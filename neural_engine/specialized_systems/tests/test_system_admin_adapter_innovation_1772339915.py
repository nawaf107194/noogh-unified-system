import pytest
from typing import Dict, Any

class SystemAdminAdapter:
    def __init__(self):
        self.observation_history = []
        self.max_history = 100

    def get_status(self) -> Dict[str, Any]:
        """Get adapter status"""
        return {
            "adapter": "SystemAdmin",
            "status": "operational",
            "observations_stored": len(self.observation_history),
            "max_history": self.max_history
        }

# Test cases
def test_get_status_happy_path():
    adapter = SystemAdminAdapter()
    result = adapter.get_status()
    assert isinstance(result, dict)
    assert result["adapter"] == "SystemAdmin"
    assert result["status"] == "operational"
    assert result["observations_stored"] == 0
    assert result["max_history"] == 100

def test_get_status_with_observations():
    adapter = SystemAdminAdapter()
    adapter.observation_history.extend(["observation1", "observation2"])
    result = adapter.get_status()
    assert result["observations_stored"] == 2

def test_get_status_empty_history():
    adapter = SystemAdminAdapter()
    adapter.observation_history.clear()
    result = adapter.get_status()
    assert result["observations_stored"] == 0

def test_get_status_max_history():
    adapter = SystemAdminAdapter()
    adapter.max_history = 50
    result = adapter.get_status()
    assert result["max_history"] == 50

# Note: There are no error cases or async behavior in this function, so those test cases are not needed.