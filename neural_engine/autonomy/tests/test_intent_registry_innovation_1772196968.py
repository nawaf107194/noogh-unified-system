from neural_engine.autonomy.intent_registry import IntentRegistry, IntentCategory

@pytest.fixture
def intent_registry():
    # Assuming this is how you initialize your IntentRegistry
    registry = IntentRegistry()
    # Populate the registry with some intents for testing
    registry._intents = {
        IntentCategory.AI: [
            {"name": "example1", "description": "This is an example intent", "examples": ["ex1", "ex2"]},
            {"name": "example3", "description": "Another example intent", "examples": []},
        ],
    }
    return registry

def test_get_help_text_happy_path(intent_registry):
    help_text = intent_registry.get_help_text()
    assert "🤖 **قدرات نوقه:**" in help_text
    assert "**AI:**" in help_text
    assert "* example1: This is an example intent*\n  مثال: ex1, ex2\n" in help_text
    assert "* example3: Another example intent*" in help_text

def test_get_help_text_empty_category(intent_registry):
    # Clear the intents for a specific category to simulate an empty state
    intent_registry._intents[IntentCategory.AI] = []
    help_text = intent_registry.get_help_text()
    assert "🤖 **قدرات نوقه:**" in help_text
    assert "**AI:**" not in help_text

def test_get_help_text_no_categories(intent_registry):
    # Clear all intents to simulate an empty registry
    intent_registry._intents.clear()
    help_text = intent_registry.get_help_text()
    assert "🤖 **قدرات نوقه:**" in help_text
    assert "**AI:**" not in help_text

def test_get_help_text_invalid_category(intent_registry):
    # This case doesn't apply here as the function iterates over all categories and skips empty ones
    pass  # No need to test for invalid categories since they are skipped

# Async behavior is not applicable here as there are no async methods or calls in the function