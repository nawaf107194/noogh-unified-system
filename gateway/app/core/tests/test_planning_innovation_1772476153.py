import pytest
from typing import Optional, List
from gateway.app.core.planning import PlanStep, get_next_step

class MockPlanStep:
    def __init__(self, id: str, status: str, dependencies: Optional[List[str]] = None):
        self.id = id
        self.status = status
        self.dependencies = dependencies if dependencies is not None else []

def test_happy_path():
    steps = [
        MockPlanStep("1", "completed"),
        MockPlanStep("2", "pending", ["1"]),
        MockPlanStep("3", "pending", ["4"])
    ]
    result = get_next_step(steps)
    assert result.id == "2"

def test_empty_list():
    steps: List[MockPlanStep] = []
    result = get_next_step(steps)
    assert result is None

def test_none_input():
    result = get_next_step(None)
    assert result is None

def test_invalid_steps_type():
    steps = ["not", "a", "list"]
    result = get_next_step(steps)
    assert result is None

def test_pending_step_with_unmet_dependency():
    steps = [
        MockPlanStep("1", "completed"),
        MockPlanStep("2", "pending", ["3"]),
        MockPlanStep("3", "completed")
    ]
    result = get_next_step(steps)
    assert result is None

def test_invalid_step_type():
    steps = [
        MockPlanStep("1", "completed"),
        "not_a_plan_step",
        MockPlanStep("2", "pending", ["1"])
    ]
    result = get_next_step(steps)
    assert result is None

def test_no_pending_steps():
    steps = [
        MockPlanStep("1", "completed"),
        MockPlanStep("2", "completed")
    ]
    result = get_next_step(steps)
    assert result is None