import pytest

from gateway.app.plugins.loader import PluginLoader, PluginRegistry

class TestPluginLoader:

    @pytest.mark.parametrize("key", [
        "valid_key",
        "another_valid_key123",
        "yet_another_key_with_special_chars_!@#$%^&*()_+"
    ])
    def test_happy_path(self, key):
        loader = PluginLoader(key)
        assert loader.signing_key == key
        assert isinstance(loader.registry, PluginRegistry)

    @pytest.mark.parametrize("key", [
        "",
        None,
        " ",
        "\t",
        "\n",
        "1234567890"
    ])
    def test_edge_cases(self, key):
        loader = PluginLoader(key)
        assert loader.signing_key is None
        assert isinstance(loader.registry, PluginRegistry)

    @pytest.mark.parametrize("key", [
        {"not": "a string"},
        ["list", "of", "strings"],
        (1, 2, 3),
        {1: "one", 2: "two"}
    ])
    def test_error_cases(self, key):
        loader = PluginLoader(key)
        assert loader.signing_key is None
        assert isinstance(loader.registry, PluginRegistry)

@pytest.fixture(scope="module")
def plugin_registry():
    return PluginRegistry.get_instance()