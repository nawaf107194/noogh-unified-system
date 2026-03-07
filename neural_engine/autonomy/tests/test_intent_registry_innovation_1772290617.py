import pytest

from neural_engine.autonomy.intent_registry import IntentRegistry, Intent, logger


class MockIntent(Intent):
    def __init__(self, name: str):
        super().__init__(name)


@pytest.fixture
def intent_registry():
    return IntentRegistry()


def test_init_happy_path(intent_registry):
    assert isinstance(intent_registry.intents, dict)
    assert len(intent_registry.intents) > 0
    logger.info.assert_called_once()


def test_init_empty_intents(intent_registry):
    old_intents = intent_registry.intents.copy()
    intent_registry._register_default_intents = lambda: []
    intent_registry.__init__()
    assert intent_registry.intents == {}
    assert len(intent_registry.intents) == 0
    logger.info.assert_called_once()


def test_init_none_intents(intent_registry):
    old_intents = intent_registry.intents.copy()
    intent_registry._register_default_intents = lambda: None
    intent_registry.__init__()
    assert intent_registry.intents == {}
    assert len(intent_registry.intents) == 0
    logger.info.assert_called_once()


def test_init_invalid_input_type(intent_registry):
    old_intents = intent_registry.intents.copy()
    intent_registry._register_default_intents = lambda: "not a list"
    with pytest.raises(TypeError):
        intent_registry.__init__()


def test_init_async_behavior(intent_registry, monkeypatch):
    mock_register = asyncio.coroutine(lambda: None)
    monkeypatch.setattr(intent_registry, "_register_default_intents", mock_register)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(intent_registry.__init__())
    assert intent_registry.intents == {}
    logger.info.assert_called_once()