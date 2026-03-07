import pytest
from gateway.app.core.tool_execution_bridge import ToolExecutionBridge, ModulePriority, ModuleMetadata

@pytest.fixture
def bridge():
    return ToolExecutionBridge()

def test_happy_path(bridge):
    assert bridge.registry is None
    assert bridge.actuators is None
    assert isinstance(bridge._metadata, ModuleMetadata)
    assert bridge._metadata.name == "ToolExecutionBridge"
    assert bridge._metadata.version == "1.1.0"
    assert bridge._metadata.description == "Executes tools with XAI justification enforcement"
    assert bridge._metadata.dependencies == ["unified_core.tool_registry", "unified_core.core.actuators"]
    assert bridge._metadata.priority == ModulePriority.CRITICAL
    assert bridge._metadata.capabilities == ["execution", "actuation", "system_control", "governance"]

def test_missing_metadata_fields():
    with pytest.raises(TypeError) as excinfo:
        metadata = ModuleMetadata(name=None, version="1.1.0", description="", dependencies=[], priority=ModulePriority.CRITICAL, capabilities=[])
    assert str(excinfo.value) == "The 'name' field in _metadata must be a string."

def test_invalid_dependency_type():
    with pytest.raises(TypeError) as excinfo:
        metadata = ModuleMetadata(name="ToolExecutionBridge", version="1.1.0", description="", dependencies=[123], priority=ModulePriority.CRITICAL, capabilities=[])
    assert str(excinfo.value) == "The 'dependencies' field in _metadata must be a list of strings."

def test_invalid_priority_type():
    with pytest.raises(TypeError) as excinfo:
        metadata = ModuleMetadata(name="ToolExecutionBridge", version="1.1.0", description="", dependencies=["unified_core.tool_registry"], priority="CRITICAL", capabilities=[])
    assert str(excinfo.value) == "The 'priority' field in _metadata must be an instance of ModulePriority."

def test_invalid_capability_type():
    with pytest.raises(TypeError) as excinfo:
        metadata = ModuleMetadata(name="ToolExecutionBridge", version="1.1.0", description="", dependencies=["unified_core.tool_registry"], priority=ModulePriority.CRITICAL, capabilities=[123])
    assert str(excinfo.value) == "The 'capabilities' field in _metadata must be a list of strings."