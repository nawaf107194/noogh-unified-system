import pytest
from unified_core.evolution.neuron_learning import NeuronLearning

def test_get_stats_happy_path():
    neuron = NeuronLearning()
    neuron._total_lessons = 10
    neuron._success_lessons = 8
    neuron._failure_lessons = 2
    neuron._save_counter = 5
    assert neuron.get_stats() == {
        "total_lessons": 10,
        "success_lessons": 8,
        "failure_lessons": 2,
        "save_counter": 5,
    }

def test_get_stats_empty_values():
    neuron = NeuronLearning()
    neuron._total_lessons = 0
    neuron._success_lessons = 0
    neuron._failure_lessons = 0
    neuron._save_counter = 0
    assert neuron.get_stats() == {
        "total_lessons": 0,
        "success_lessons": 0,
        "failure_lessons": 0,
        "save_counter": 0,
    }

def test_get_stats_none_values():
    neuron = NeuronLearning()
    neuron._total_lessons = None
    neuron._success_lessons = None
    neuron._failure_lessons = None
    neuron._save_counter = None
    assert neuron.get_stats() == {
        "total_lessons": None,
        "success_lessons": None,
        "failure_lessons": None,
        "save_counter": None,
    }

def test_get_stats_mixed_values():
    neuron = NeuronLearning()
    neuron._total_lessons = 10
    neuron._success_lessons = None
    neuron._failure_lessons = 2
    neuron._save_counter = "five"
    assert neuron.get_stats() == {
        "total_lessons": 10,
        "success_lessons": None,
        "failure_lessons": 2,
        "save_counter": "five",
    }