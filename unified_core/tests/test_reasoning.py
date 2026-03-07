import pytest

from unified_core.reasoning import mark_step_complete, Plan

class TestMarkStepComplete:

    def test_happy_path(self):
        plan = Plan(steps=[{"status": "pending"}, {"status": "pending"}], current_step_index=0)
        assert mark_step_complete(plan) is None
        assert plan.steps[0]["status"] == "completed"
        assert plan.current_step_index == 1

    def test_edge_case_empty_plan(self):
        plan = Plan(steps=[], current_step_index=0)
        result = mark_step_complete(plan)
        assert result is None
        assert plan.steps == []
        assert plan.current_step_index == 0

    def test_edge_case_none_plan(self):
        plan = None
        result = mark_step_complete(plan)
        assert result is None

    def test_error_case_invalid_plan(self):
        invalid_plan = "not a plan"
        result = mark_step_complete(invalid_plan)
        assert result is None