import pytest

from gateway.app.plugins.registry import Registry

def test_registry_init_happy_path():
    registry = Registry()
    assert isinstance(registry.plugins, dict)
    assert isinstance(registry.tools, dict)

def test_registry_init_edge_case_empty_plugins():
    registry = Registry(plugins={})
    assert isinstance(registry.plugins, dict)
    assert len(registry.plugins) == 0

def test_registry_init_edge_case_none_plugins():
    with pytest.raises(TypeError):
        Registry(plugins=None)

def test_registry_init_edge_case_empty_tools():
    registry = Registry(tools={})
    assert isinstance(registry.tools, dict)
    assert len(registry.tools) == 0

def test_registry_init_edge_case_none_tools():
    with pytest.raises(TypeError):
        Registry(tools=None)