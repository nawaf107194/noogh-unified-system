import pytest
from unittest.mock import patch, Mock
from time import time

# Assuming the class is named InnovationEngine and it's imported from the module
from unified_core.evolution.innovation_engine import InnovationEngine

@pytest.fixture
def innovation_engine():
    engine = InnovationEngine()
    engine._last_innovation_time = {}
    engine._cooldown_hours = 24  # Example cooldown hours
    return engine

def test_can_innovate_happy_path(innovation_engine):
    innovation_engine._last_innovation_time['test_type'] = time() - 25 * 3600
    assert innovation_engine._can_innovate('test_type') == True

def test_can_innovate_on_cooldown(innovation_engine):
    innovation_engine._last_innovation_time['test_type'] = time() - 23 * 3600
    assert innovation_engine._can_innovate('test_type') == False

def test_can_innovate_empty_last_innovation_time(innovation_engine):
    assert innovation_engine._can_innovate('test_type') == True

def test_can_innovate_none_innovation_type(innovation_engine):
    with pytest.raises(TypeError):
        innovation_engine._can_innovate(None)

def test_can_innovate_invalid_innovation_type(innovation_engine):
    with pytest.raises(TypeError):
        innovation_engine._can_innovate(123)

def test_can_innovate_boundary_case_zero_cooldown(innovation_engine):
    innovation_engine._cooldown_hours = 0
    innovation_engine._last_innovation_time['test_type'] = time() - 24 * 3600
    assert innovation_engine._can_innovate('test_type') == True

def test_can_innovate_boundary_case_negative_cooldown(innovation_engine):
    innovation_engine._cooldown_hours = -1
    innovation_engine._last_innovation_time['test_type'] = time() - 24 * 3600
    assert innovation_engine._can_innovate('test_type') == True

# Since the function does not involve any asynchronous operations,
# there is no need to test async behavior.