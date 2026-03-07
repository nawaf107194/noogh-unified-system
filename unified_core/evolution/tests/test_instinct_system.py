import pytest
from typing import Dict, Any

class MockObserver:
    def load_all(self):
        return [
            {"event_type": "promoted"},
            {"event_type": "failed"},
            {"event_type": "rejected"},
            {"event_type": "dedup_rejected"}
        ]

class MockInstincts:
    def __init__(self):
        self._instincts = [
            {"instinct_id": 1, "confidence": 0.9, "action": "action1"},
            {"instinct_id": 2, "confidence": 0.7, "action": "action2"}
        ]

    def __len__(self):
        return len(self._instincts)

    def __getitem__(self, index):
        return self._instincts[index]

class MockEvolutionSystem:
    def evolve(self):
        pass

def test_summary_happy_path():
    observer = MockObserver()
    instincts = MockInstincts()
    evolution_system = MockEvolutionSystem()
    evolution_system._observer = observer
    evolution_system._instincts = instincts

    result = evolution_system.summary()

    assert isinstance(result, dict)
    assert len(result) == 5
    assert result["total_observations"] == 4
    assert result["total_instincts"] == 2
    assert result["promoted"] == 1
    assert result["failed"] == 1
    assert result["rejected"] == 2
    assert len(result["high_confidence_instincts"]) == 1
    assert result["high_confidence_instincts"][0] == {"id": 1, "confidence": 0.9, "action": "action1"}

def test_summary_empty_observations():
    observer = MockObserver()
    observer.load_all.return_value = []
    instincts = MockInstincts()
    evolution_system = MockEvolutionSystem()
    evolution_system._observer = observer
    evolution_system._instincts = instincts

    result = evolution_system.summary()

    assert isinstance(result, dict)
    assert len(result) == 5
    assert result["total_observations"] == 0
    assert result["total_instincts"] == 2
    assert result["promoted"] == 0
    assert result["failed"] == 0
    assert result["rejected"] == 0
    assert len(result["high_confidence_instincts"]) == 1

def test_summary_empty_instincts():
    observer = MockObserver()
    instincts = MockInstincts()
    instincts.__len__.return_value = 0
    evolution_system = MockEvolutionSystem()
    evolution_system._observer = observer
    evolution_system._instincts = instincts

    result = evolution_system.summary()

    assert isinstance(result, dict)
    assert len(result) == 5
    assert result["total_observations"] == 4
    assert result["total_instincts"] == 0
    assert result["promoted"] == 1
    assert result["failed"] == 1
    assert result["rejected"] == 2
    assert len(result["high_confidence_instincts"]) == 0

def test_summary_no_high_confidence_instincts():
    observer = MockObserver()
    instincts = MockInstincts()
    instincts.__getitem__.return_value = {"instinct_id": 1, "confidence": 0.7, "action": "action1"}
    evolution_system = MockEvolutionSystem()
    evolution_system._observer = observer
    evolution_system._instincts = instincts

    result = evolution_system.summary()

    assert isinstance(result, dict)
    assert len(result) == 5
    assert result["total_observations"] == 4
    assert result["total_instincts"] == 2
    assert result["promoted"] == 1
    assert result["failed"] == 1
    assert result["rejected"] == 2
    assert len(result["high_confidence_instincts"]) == 0