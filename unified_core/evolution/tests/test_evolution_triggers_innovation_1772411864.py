import pytest

class MockScheduledTrigger:
    def report_duration(self, duration_seconds):
        pass

class TestEvolutionTriggers:
    def test_happy_path(self):
        triggers = [MockScheduledTrigger(), MockScheduledTrigger()]
        evolution_triggers = EvolutionTriggers(triggers)
        evolution_triggers.report_cycle_duration(10.5)
        
    def test_edge_case_empty_list(self):
        evolution_triggers = EvolutionTriggers([])
        evolution_triggers.report_cycle_duration(10.5)
        
    def test_edge_case_none_input(self):
        class TriggersWithNone:
            triggers = [None, MockScheduledTrigger()]
            
        evolution_triggers = EvolutionTriggers(TriggersWithNone.triggers)
        evolution_triggers.report_cycle_duration(10.5)
        
    def test_error_case_invalid_input(self):
        class TriggersWithInvalidInput:
            triggers = [MockScheduledTrigger(), "not a trigger"]
            
        evolution_triggers = EvolutionTriggers(TriggersWithInvalidInput.triggers)
        with pytest.raises(TypeError):
            evolution_triggers.report_cycle_duration(10.5)

class EvolutionTriggers:
    def __init__(self, triggers):
        self.triggers = triggers

    def report_cycle_duration(self, duration_seconds: float):
        """Feed cycle duration to the ScheduledTrigger for adaptive cooldown."""
        for t in self.triggers:
            if isinstance(t, MockScheduledTrigger):
                t.report_duration(duration_seconds)
                break