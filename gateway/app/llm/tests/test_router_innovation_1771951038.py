import pytest

from gateway.app.llm.router import Router, settings

class MockSettings:
    CLOUD_API_KEY = "fake_api_key"

def test_route_happy_path():
    router = Router(default_mode="local")
    assert router.route("A normal query") == "local"
    assert router.route("Another normal query", mode="cloud") == "cloud"

def test_route_edge_cases():
    router = Router(default_mode="local")
    assert router.route("") == "local"
    assert router.route(None) == "local"
    assert router.route("query", mode="invalid") == "local"
    assert router.route("query", allow_exec=True) == "local"

def test_route_auto_logic_local():
    router = Router(default_mode="local")
    assert router.route("EXEC request", allow_exec=False) == "local"
    assert router.route("Sensitive data", _is_sensitive=lambda x: True, allow_exec=False) == "local"

def test_route_auto_logic_cloud():
    settings.CLOUD_API_KEY = MockSettings.CLOUD_API_KEY
    router = Router(default_mode="local")
    assert router.route("query requiring cloud capabilities", _needs_cloud_capabilities=lambda x: True) == "cloud"

def test_route_default_local():
    router = Router(default_mode="local")
    assert router.route("default query") == "local"