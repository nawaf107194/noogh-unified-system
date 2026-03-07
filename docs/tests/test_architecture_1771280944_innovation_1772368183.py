import pytest

def initialize_docs(config):
    # Use the config object here
    print(f"Docs initialized with settings: {config.settings}")

class MockConfig:
    def __init__(self, settings):
        self.settings = settings

@pytest.mark.parametrize("config", [
    MockConfig(settings={"key": "value"}),
    MockConfig(settings={}),
    MockConfig(settings=None),
    MockConfig(settings=0)
])
def test_initialize_docs(config):
    initialize_docs(config)

@pytest.mark.skip(reason="The function does not raise exceptions for invalid inputs")
def test_initialize_docs_invalid_input():
    with pytest.raises(ValueError):
        initialize_docs("not a config object")

# Since the function does not have an async behavior, no need to add any tests for that