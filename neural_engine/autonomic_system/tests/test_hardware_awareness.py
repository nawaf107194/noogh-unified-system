import pytest
from unittest.mock import patch, MagicMock
import psutil
from neural_engine.autonomic_system.hardware_awareness import HardwareAwareness

def test_introspect_sensors_happy_path():
    hw = HardwareAwareness()
    
    with patch('psutil.sensors_temperatures', return_value={
        "cpu": [
            psutil._SensorEntry(label="CPU Core 0", current=50.0, high=None, critical=None)
        ]
    }), \
         patch('psutil.sensors_fans', return_value={
             "fan": [
                 psutil._SensorEntry(label="Fan 1", current=2000)
             ]
         }), \
         patch('psutil.sensors_battery', return_value=psutil._Battery(percent=85, power_plugged=True, secsleft=3600)):
        
        result = hw._introspect_sensors()
        
        assert result == {
            "temperatures": {"cpu": [{"label": "CPU Core 0", "current_c": 50.0, "high_c": None, "critical_c": None}]},
            "fans": {"fan": [{"label": "Fan 1", "rpm": 2000}]},
            "battery": {
                "percent": 85,
                "plugged_in": True,
                "time_left_sec": 3600
            }
        }

def test_introspect_sensors_edge_cases():
    hw = HardwareAwareness()
    
    with patch('psutil.sensors_temperatures', return_value=None), \
         patch('psutil.sensors_fans', return_value=None), \
         patch('psutil.sensors_battery', return_value=None):
        
        result = hw._introspect_sensors()
        
        assert result == {
            "temperatures": {},
            "fans": {},
            "battery": None
        }

def test_introspect_sensors_error_cases():
    hw = HardwareAwareness()
    
    with patch('psutil.sensors_temperatures', side_effect=Exception("Sensor error")), \
         patch('psutil.sensors_fans', side_effect=Exception("Sensor error")), \
         patch('psutil.sensors_battery', side_effect=Exception("Sensor error")):
        
        result = hw._introspect_sensors()
        
        assert result == {
            "temperatures": {},
            "fans": {},
            "battery": None
        }