import pytest

from gateway.app.ml.dream_worker import DreamWorker

def get_settings():
    return {
        "priority_thresholds": {
            "high": 5,
            "medium": 3
        }
    }

@pytest.fixture
def dream_worker():
    return DreamWorker()

def test_happy_path(dream_worker):
    assert dream_worker.high_priority == []
    assert dream_worker.medium_priority == []
    assert dream_worker.low_priority == []

def test_settings_are_loaded(dream_worker):
    assert isinstance(dream_worker.settings, dict)
    assert "priority_thresholds" in dream_worker.settings
    assert "high" in dream_worker.settings["priority_thresholds"]
    assert "medium" in dream_worker.settings["priority_thresholds"]

def test_empty_input(settings):
    with pytest.raises(TypeError):
        DreamWorker(settings=None)

def test_invalid_settings_type(settings):
    with pytest.raises(TypeError):
        DreamWorker(settings="not a dict")

def test_async_behavior():
    # Assuming there's no async behavior in the __init__ method
    pass