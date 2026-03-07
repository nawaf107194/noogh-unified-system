import pytest

class TestReasoningGetNextStep:

    @pytest.fixture
    def reasoning(self):
        from unified_core.reasoning import Reasoning
        return Reasoning()

    @pytest.mark.parametrize("plan, expected", [
        (Plan(steps=[PlanStep(action="step1"), PlanStep(action="step2")], current_step_index=0), PlanStep(action="step1")),
        (Plan(steps=[PlanStep(action="step3"), PlanStep(action="step4")], current_step_index=1), PlanStep(action="step4")),
    ])
    def test_happy_path(self, reasoning, plan, expected):
        result = reasoning.get_next_step(plan)
        assert result == expected

    @pytest.mark.parametrize("plan, expected", [
        (Plan(steps=[], current_step_index=0), None),
        (Plan(steps=[PlanStep(action="step1")], current_step_index=len(PlanStep(action="step1").steps)), None),
    ])
    def test_edge_cases(self, reasoning, plan, expected):
        result = reasoning.get_next_step(plan)
        assert result == expected

    @pytest.mark.parametrize("plan", [
        (None),
        ("not a plan"),
        (5),
    ])
    def test_error_cases(self, reasoning, plan):
        with pytest.raises(TypeError):
            reasoning.get_next_step(plan)

class Plan:
    def __init__(self, steps=None, current_step_index=0):
        self.steps = steps if steps is not None else []
        self.current_step_index = current_step_index

class PlanStep:
    def __init__(self, action):
        self.action = action