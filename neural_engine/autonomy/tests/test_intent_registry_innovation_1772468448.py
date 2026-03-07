import pytest
from neural_engine.autonomy.intent_registry import IntentRegistry, IntentCategory

@pytest.fixture
def intent_registry():
    registry = IntentRegistry()
    registry._register_default_intents()
    return registry

def test_happy_path(intent_registry):
    intents = list(intent_registry.intents.values())
    
    # Check if all default intents are registered
    assert len(intents) == 15
    
    # Check specific intent details
    greet_intent = next((i for i in intents if i.id == "greet"), None)
    assert greet_intent is not None
    assert greet_intent.name == "Greeting"
    assert greet_intent.category == IntentCategory.GREETING
    assert len(greet_intent.patterns) == 1
    
    who_are_you_intent = next((i for i in intents if i.id == "who_are_you"), None)
    assert who_are_you_intent is not None
    assert who_are_you_intent.name == "Identity Question"
    assert who_are_you_intent.category == IntentCategory.IDENTITY
    assert len(who_are_you_intent.patterns) == 2
    
    check_memory_intent = next((i for i in intents if i.id == "check_memory"), None)
    assert check_memory_intent is not None
    assert check_memory_intent.name == "Check Memory"
    assert check_memory_intent.category == IntentCategory.SYSTEM_MONITOR
    assert len(check_memory_intent.patterns) == 2
    
    run_tests_intent = next((i for i in intents if i.id == "run_tests"), None)
    assert run_tests_intent is not None
    assert run_tests_intent.name == "Run Tests"
    assert run_tests_intent.category == IntentCategory.DEVELOPMENT
    assert len(run_tests_intent.patterns) == 1
    
def test_edge_cases(intent_registry):
    # Check if no intents are registered when called again
    initial_count = len(intent_registry.intents)
    intent_registry._register_default_intents()
    final_count = len(intent_registry.intents)
    assert initial_count == final_count

    # Check if empty patterns do not register intents
    registry = IntentRegistry()
    registry.register(Intent(
        id="empty_pattern",
        name="Empty Pattern",
        category=IntentCategory.GREETING,
        patterns=[],
        action="direct_response",
        description="Empty pattern"
    ))
    assert "empty_pattern" not in registry.intents

def test_error_cases(intent_registry):
    # Error cases are not applicable as the function does not explicitly raise exceptions
    pass

# Note: Async behavior is not applicable here as there are no async functions or methods being tested.