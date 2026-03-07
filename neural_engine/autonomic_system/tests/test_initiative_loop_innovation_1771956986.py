import pytest

from neural_engine.autonomic_system.initiative_loop import get_initiative_loop, InitiativeLoop
from unittest.mock import patch

@pytest.fixture(autouse=True)
def reset_instance():
    """Reset the singleton instance before each test."""
    from neural_engine.autonomic_system.initiative_loop import _loop_instance
    _loop_instance = None

def test_get_initiative_loop_happy_path():
    interval = 60
    loop = get_initiative_loop(interval=interval)
    assert isinstance(loop, InitiativeLoop)
    assert loop.interval == interval

def test_get_initiative_loop_default_interval():
    loop = get_initiative_loop()
    assert isinstance(loop, InitiativeLoop)
    assert loop.interval == 60

def test_get_initiative_loop_single_instance():
    loop1 = get_initiative_loop(interval=60)
    loop2 = get_initiative_loop(interval=60)
    assert loop1 is loop2
    assert loop1.interval == loop2.interval

@patch('neural_engine.autonomic_system.initiative_loop.InitiativeLoop')
def test_get_initiative_loop_with_invalid_interval(mock_initiative_loop):
    with pytest.raises(ValueError) as exc_info:
        get_initiative_loop(interval=-1)
    assert str(exc_info.value) == "Interval must be a positive integer"

@patch('neural_engine.autonomic_system.initiative_loop.InitiativeLoop')
def test_get_initiative_loop_with_non_integer_interval(mock_initiative_loop):
    with pytest.raises(ValueError) as exc_info:
        get_initiative_loop(interval="10")
    assert str(exc_info.value) == "Interval must be a positive integer"