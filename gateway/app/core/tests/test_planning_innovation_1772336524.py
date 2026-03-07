import pytest

from gateway.app.core.planning import Planning, PlanStep

@pytest.fixture
def planning_instance():
    steps = [
        PlanStep(id="step1", status="completed", dependencies=["dep1"]),
        PlanStep(id="step2", status="pending", dependencies=["dep1"]),
        PlanStep(id="step3", status="pending", dependencies=["dep2"])
    ]
    return Planning(steps=steps)

def test_happy_path(planning_instance):
    next_step = planning_instance.get_next_step()
    assert next_step.id == "step2"

def test_empty_steps():
    steps = []
    planning = Planning(steps=steps)
    assert planning.get_next_step() is None

def test_none_steps():
    planning = Planning(steps=None)
    assert planning.get_next_step() is None

def test_invalid_steps_type():
    steps = "not a list"
    with pytest.raises(ValueError) as exc_info:
        Planning(steps=steps).get_next_step()
    assert str(exc_info.value) == "self.steps must be a list"

def test_invalid_step_instance():
    invalid_steps = [
        PlanStep(id="step1", status="completed", dependencies=["dep1"]),
        {"id": "step2", "status": "pending", "dependencies": ["dep1"]}
    ]
    with pytest.raises(ValueError) as exc_info:
        Planning(steps=invalid_steps).get_next_step()
    assert str(exc_info.value) == "All steps must be instances of PlanStep"

def test_pending_step_with_unmet_dependency():
    steps = [
        PlanStep(id="step1", status="completed", dependencies=["dep1"]),
        PlanStep(id="step2", status="pending", dependencies=["dep2"])
    ]
    planning = Planning(steps=steps)
    assert planning.get_next_step() is None

def test_pending_step_with_mixed_dependencies():
    steps = [
        PlanStep(id="step1", status="completed", dependencies=["dep1"]),
        PlanStep(id="step2", status="pending", dependencies=["dep1", "dep2"])
    ]
    planning = Planning(steps=steps)
    assert planning.get_next_step() is None