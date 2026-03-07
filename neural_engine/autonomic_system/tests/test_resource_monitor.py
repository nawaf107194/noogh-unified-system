import pytest

from neural_engine.autonomic_system.resource_monitor import ResourceMonitor
import logging

def test_resource_monitor_init_happy_path(caplog):
    caplog.set_level(logging.INFO)
    
    # Create an instance of the class to trigger the __init__ method
    resource_monitor = ResourceMonitor()
    
    # Assert that the logger.info message was called once
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "ResourceMonitor initialized."

def test_resource_monitor_init_no_logger():
    with pytest.raises(AttributeError):
        class MockLogger:
            def info(self, *args, **kwargs):
                pass
        
        resource_monitor = ResourceMonitor()