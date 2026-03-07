import pytest
from typing import List, Optional
from unittest.mock import Mock
from gateway.app.core.models import PlanStep
from gateway.app.core.planning import Planner

@pytest.fixture
def plan_step():
    return PlanStep(id="test", dependencies=[], status="pending")

@pytest.fixture
def completed_plan_step():
    return PlanStep(id="completed", status="completed")

@pytest.fixture
def planner():
    return Planner(steps=[])

def test_get_next_step_happy_path(planner: Planner, plan_step: PlanStep, completed_plan_step: PlanStep):
    """Test getting next step when dependencies are met"""
    plan_step.dependencies = ["completed"]
    planner.steps = [completed_plan_step, plan_step]
    
    result = planner.get_next_step()
    assert result == plan_step

def test_get_next_step_empty_steps(planner: Planner):
    """Test with empty steps list"""
    planner.steps = []
    assert planner.get_next_step() is None

def test_get_next_step_all_completed(planner: Planner, completed_plan_step: PlanStep):
    """Test when all steps are completed"""
    planner.steps = [completed_plan_step, PlanStep(id="another", status="completed")]
    assert planner.get_next_step() is None

def test_get_next_step_invalid_steps_type(planner: Planner):
    """Test when steps is not a list"""
    planner.steps = None
    with pytest.raises(ValueError):
        planner.get_next_step()

def test_get_next_step_invalid_step_type(planner: Planner):
    """Test when a step is not PlanStep instance"""
    planner.steps = [Mock()]  # Invalid step type
    with pytest.raises(ValueError):
        planner.get_next_step()

def test_get_next_step_invalid_dependencies(planner: Planner, plan_step: PlanStep):
    """Test when dependencies are invalid"""
    plan_step.dependencies = [123]  # Non-string dependency
    planner.steps = [plan_step]
    with pytest.raises(ValueError):
        planner.get_next_step()