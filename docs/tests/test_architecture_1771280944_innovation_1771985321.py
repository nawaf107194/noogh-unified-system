import pytest

class MockSettings:
    def __init__(self, value):
        self.value = value

def test_init_happy_path():
    settings = MockSettings(value="test_settings")
    instance = ExampleClass(settings)
    assert instance.settings == settings

def test_init_edge_case_none():
    instance = ExampleClass(None)
    assert instance.settings is None

def test_init_edge_case_empty():
    settings = MockSettings(value="")
    instance = ExampleClass(settings)
    assert instance.settings == settings

def test_init_error_case_invalid_input():
    with pytest.raises(TypeError):
        instance = ExampleClass("not a valid settings object")

class ExampleClass:
    def __init__(self, settings):
        self.settings = settings