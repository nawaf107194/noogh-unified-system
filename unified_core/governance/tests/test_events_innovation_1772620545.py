import pytest
from unified_core.governance.events import get_observability_bus
from unified_core.governance.events import ObservabilityBus

def test_get_observability_bus_happy_path():
    """Test happy path - verify function returns ObservabilityBus instance"""
    bus = get_observability_bus()
    assert isinstance(bus, ObservabilityBus), "Returned object is not an instance of ObservabilityBus"

def test_get_observability_bus_same_instance():
    """Test that function consistently returns the same bus instance"""
    bus1 = get_observability_bus()
    bus2 = get_observability_bus()
    assert bus1 is bus2, "Function did not return the same instance on consecutive calls"