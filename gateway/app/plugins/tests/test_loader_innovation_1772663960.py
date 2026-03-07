import pytest
from src.gateway.app.plugins.loader import PluginLoader
from src.gateway.app.plugins.registry import PluginRegistry

def test_init_with_valid_key():
    key = "test_key"
    loader = PluginLoader(key)
    assert loader.signing_key == key
    assert isinstance(loader.registry, PluginRegistry)

def test_init_with_empty_string():
    key = ""
    loader = PluginLoader(key)
    assert loader.signing_key == key
    assert isinstance(loader.registry, PluginRegistry)

def test_init_with_none():
    loader = PluginLoader(None)
    assert loader.signing_key is None
    assert isinstance(loader.registry, PluginRegistry)