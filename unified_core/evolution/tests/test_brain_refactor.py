import pytest

from unified_core.evolution.brain_refactor import BrainRefactor  # Adjust the import path as necessary

@pytest.fixture
def brain_refactor():
    return BrainRefactor()

def test_get_stats_happy_path(brain_refactor):
    brain_refactor.requests_made = 10
    brain_refactor.successful_refactors = 8
    brain_refactor.failed_refactors = 2
    
    expected_stats = {
        "requests_made": 10,
        "successful": 8,
        "failed": 2,
        "success_rate": 0.8
    }
    
    assert brain_refactor.get_stats() == expected_stats

def test_get_stats_empty_values(brain_refactor):
    brain_refactor.requests_made = 0
    brain_refactor.successful_refactors = 0
    brain_refactor.failed_refactors = 0
    
    expected_stats = {
        "requests_made": 0,
        "successful": 0,
        "failed": 0,
        "success_rate": 0
    }
    
    assert brain_refactor.get_stats() == expected_stats

def test_get_stats_with_no_requests(brain_refactor):
    brain_refactor.requests_made = 0
    brain_refactor.successful_refactors = 5
    brain_refactor.failed_refactors = 1
    
    expected_stats = {
        "requests_made": 0,
        "successful": 5,
        "failed": 1,
        "success_rate": 0
    }
    
    assert brain_refactor.get_stats() == expected_stats

def test_get_stats_with_negative_values(brain_refactor):
    brain_refactor.requests_made = -5
    brain_refactor.successful_refactors = -2
    brain_refactor.failed_refactors = -3
    
    expected_stats = {
        "requests_made": -5,
        "successful": -2,
        "failed": -3,
        "success_rate": 0.4
    }
    
    assert brain_refactor.get_stats() == expected_stats

def test_get_stats_with_none_values(brain_refactor):
    brain_refactor.requests_made = None
    brain_refactor.successful_refactors = None
    brain_refactor.failed_refactors = None
    
    expected_stats = {
        "requests_made": None,
        "successful": None,
        "failed": None,
        "success_rate": 0
    }
    
    assert brain_refactor.get_stats() == expected_stats