import pytest
from neural_engine.module_interface import ModuleInterface
from neural_engine.module_status import ModuleStatus
import logging

def test_init_happy_path():
    # Test normal initialization
    module = ModuleInterface()
    
    # Check status initialization
    assert module._status == ModuleStatus.UNINITIALIZED, "Status should be UNINITIALIZED"
    
    # Check metadata initialization
    assert module._metadata is None, "Metadata should be None"
    
    # Check logger initialization
    assert isinstance(module._logger, logging.Logger), "Logger should be a logging.Logger instance"
    assert module._logger.name == module.__class__.__name__, "Logger name should match class name"

def test_init_subclass_logger():
    # Test logger name when subclassing
    class SubModuleInterface(ModuleInterface):
        pass
    
    sub_module = SubModuleInterface()
    assert sub_module._logger.name == SubModuleInterface.__name__, "Logger name should match subclass name"