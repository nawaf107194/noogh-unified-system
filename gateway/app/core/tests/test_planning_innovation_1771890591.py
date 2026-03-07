import pytest

from gateway.app.core.planning import PlanStep, get_next_step

class TestGetNextStep:

    @pytest.fixture
    def steps(self):
        completed_step = PlanStep(id="1", status="completed")
        pending_step_with_met_deps = PlanStep(id="2", status="pending", dependencies=["1"])
        pending_step_with_unmet_deps = PlanStep(id="3", status="pending", dependencies=["4"])
        return [completed_step, pending_step_with_met_deps, pending_step_with_unmet_deps]

    def test_happy_path(self, steps):
        result = get_next_step(steps)
        assert result.id == "2"

    def test_empty_steps(self):
        result = get_next_step([])
        assert result is None

    def test_none_steps(self):
        with pytest.raises(ValueError) as exc_info:
            get_next_step(None)
        assert str(exc_info.value) == "self.steps must be a list"

    def test_non_list_steps(self):
        with pytest.raises(ValueError) as exc_info:
            get_next_step("not a list")
        assert str(exc_info.value) == "self.steps must be a list"

    def test_invalid_dependency_type(self):
        invalid_step = PlanStep(id="4", status="pending", dependencies=[1])
        steps = [invalid_step]
        with pytest.raises(ValueError) as exc_info:
            get_next_step(steps)
        assert str(exc_info.value) == "Dependencies must be a list of strings"

    def test_unmet_dependency(self):
        steps = [PlanStep(id="5", status="pending", dependencies=["6"])]
        result = get_next_step(steps)
        assert result is None

    def test_all_steps_completed(self):
        steps = [PlanStep(id="7", status="completed")] * 3
        result = get_next_step(steps)
        assert result is None

    def test_mixed_steps_with_met_and_unmet_deps(self, steps):
        result = get_next_step(steps)
        assert result.id == "2"