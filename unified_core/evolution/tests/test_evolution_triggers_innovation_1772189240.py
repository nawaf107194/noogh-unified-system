import pytest

class MockTrigger:
    def __init__(self, name):
        self.name = name
        self._fire_count = 0
        self._last_fired = None

    @property
    def _total_events_fired(self):
        return 10

    def can_fire(self):
        return True

class MockEvolutionTriggers:
    def __init__(self, triggers):
        self.triggers = triggers
        self._total_events_fired = 5

def test_get_stats_happy_path():
    trigger1 = MockTrigger("trigger1")
    trigger2 = MockTrigger("trigger2")
    evolution_triggers = MockEvolutionTriggers([trigger1, trigger2])

    result = evolution_triggers.get_stats()

    expected_result = {
        "total_triggers": 2,
        "total_events_fired": 5,
        "trigger_states": {
            "trigger1": {
                "fire_count": 0,
                "last_fired": None,
                "can_fire": True
            },
            "trigger2": {
                "fire_count": 0,
                "last_fired": None,
                "can_fire": True
            }
        }
    }

    assert result == expected_result

def test_get_stats_empty_triggers():
    evolution_triggers = MockEvolutionTriggers([])

    result = evolution_triggers.get_stats()

    expected_result = {
        "total_triggers": 0,
        "total_events_fired": 5,
        "trigger_states": {}
    }

    assert result == expected_result

def test_get_stats_none_triggers():
    with pytest.raises(TypeError) as e:
        evolution_triggers = MockEvolutionTriggers(None)
        evolution_triggers.get_stats()

    assert str(e.value) == "'NoneType' object is not iterable"

def test_get_stats_invalid_trigger_type():
    class InvalidTrigger:
        pass

    trigger1 = MockTrigger("trigger1")
    trigger2 = InvalidTrigger()
    evolution_triggers = MockEvolutionTriggers([trigger1, trigger2])

    with pytest.raises(AttributeError) as e:
        evolution_triggers.get_stats()

    assert str(e.value) == "'InvalidTrigger' object has no attribute '_fire_count'"