import pytest

from neural_engine.autonomy.intent_registry import get_intent_registry, IntentRegistry

@pytest.fixture(scope="module")
def registry():
    return IntentRegistry()

@pytest.fixture(autouse=True)
def reset_registry():
    global _registry
    _registry = None
    yield

def test_get_intent_registry_happy_path(registry):
    result = get_intent_registry()
    assert isinstance(result, IntentRegistry)
    assert result is _registry

def test_get_intent_registry_edge_case_none(registry):
    result = get_intent_registry()
    assert isinstance(result, IntentRegistry)
    assert result is _registry

def test_get_intent_registry_edge_case_boundary(registry):
    result = get_intent_registry()
    assert isinstance(result, IntentRegistry)
    assert result is _registry

# Error cases are not applicable as the function does not raise any exceptions