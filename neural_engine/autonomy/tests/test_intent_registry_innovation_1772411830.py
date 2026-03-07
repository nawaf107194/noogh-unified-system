import pytest

from neural_engine.autonomy.intent_registry import get_intent_registry, IntentRegistry

@pytest.fixture(autouse=True)
def reset_registry():
    """Reset the global registry before each test."""
    global _registry
    _registry = None

def test_get_intent_registry_happy_path():
    """Test happy path with normal inputs."""
    registry1 = get_intent_registry()
    registry2 = get_intent_registry()
    
    assert registry1 is not None
    assert registry1 == registry2

def test_get_intent_registry_edge_case_none_registry():
    """Test edge case where the registry is None initially."""
    global _registry
    _registry = None  # Manually set to None for this test
    
    registry = get_intent_registry()
    
    assert registry is not None
    assert isinstance(registry, IntentRegistry)

def test_get_intent_registry_edge_case_existing_registry():
    """Test edge case where the registry already exists."""
    global _registry
    _registry = IntentRegistry()  # Manually set to an existing instance for this test
    
    registry1 = get_intent_registry()
    registry2 = get_intent_registry()
    
    assert registry1 is not None
    assert registry1 == registry2

def test_get_intent_registry_error_case_invalid_input():
    """Test error case with invalid inputs (not applicable as the function does not accept parameters)."""
    pass  # No invalid input cases in this function

# Note: As there are no async operations or specific exceptions raised, we do not need additional tests for those.