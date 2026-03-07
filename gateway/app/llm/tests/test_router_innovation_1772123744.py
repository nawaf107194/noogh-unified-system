import pytest

from gateway.app.llm.router import Router
from gateway.settings import settings

class TestRouterInit:

    @pytest.fixture
    def router(self):
        return Router()

    @pytest.mark.parametrize("settings_value", [
        "default",
        "custom",
        None,
        "",
        "boundary"
    ])
    def test_happy_path(self, router, monkeypatch, settings_value):
        monkeypatch.setattr(settings, "ROUTING_MODE", settings_value)
        assert router.default_mode == settings_value

    @pytest.mark.parametrize("settings_value", [
        {"key": "value"},
        [1, 2, 3],
        42,
        True,
        False
    ])
    def test_error_path(self, router, monkeypatch, settings_value):
        with pytest.raises(ValueError) as exc_info:
            monkeypatch.setattr(settings, "ROUTING_MODE", settings_value)
            router.default_mode = settings.ROUTING_MODE
        assert str(exc_info.value) == "Invalid routing mode"