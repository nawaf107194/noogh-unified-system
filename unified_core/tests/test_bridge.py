import pytest
from unittest.mock import patch

from unified_core.bridge import Bridge

def test_get_actuator_stats_happy_path(mocker):
    """Test get_actuator_stats with normal inputs."""
    bridge = Bridge()
    
    # Mock the _actuator_hub.get_stats() to return some stats
    mock_stats = {"total": 100, "active": 50}
    mocker.patch.object(bridge._actuator_hub, 'get_stats', return_value=mock_stats)
    
    result = bridge.get_actuator_stats()
    assert result == mock_stats

def test_get_actuator_stats_actuator_hub_not_initialized():
    """Test get_actuator_stats when ActuatorHub is not initialized."""
    bridge = Bridge()
    bridge._actuator_hub = None
    
    result = bridge.get_actuator_stats()
    assert result == {"error": "ActuatorHub not initialized"}