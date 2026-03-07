import pytest
from pydantic import ValidationError
from your_module import LLMPlanner, PLAN_SCHEMA  # Adjust the import according to your actual module structure

class TestLLMPlanner:

    @pytest.fixture
    def planner(self):
        return LLMPlanner()

    def test_validate_schema_happy_path(self, planner):
        valid_plan = {
            "step": "start",
            "action": "initialize",
            "parameters": {"key": "value"}
        }
        assert planner._validate_schema(valid_plan) is None  # No exception raised means it passed

    def test_validate_schema_empty_input(self, planner):
        with pytest.raises(ValidationError):
            planner._validate_schema({})

    def test_validate_schema_none_input(self, planner):
        with pytest.raises(TypeError):
            planner._validate_schema(None)

    def test_validate_schema_invalid_structure(self, planner):
        invalid_plan = {"wrong_key": "wrong_value"}
        with pytest.raises(ValidationError):
            planner._validate_schema(invalid_plan)

    def test_validate_schema_missing_required_field(self, planner):
        incomplete_plan = {"step": "start"}  # Assuming 'action' is required
        with pytest.raises(ValidationError):
            planner._validate_schema(incomplete_plan)

    def test_validate_schema_extra_fields(self, planner):
        extra_fields_plan = {
            "step": "start",
            "action": "initialize",
            "parameters": {"key": "value"},
            "extra_field": "extra"
        }
        if "extra_field" not in PLAN_SCHEMA["properties"]:
            with pytest.raises(ValidationError):
                planner._validate_schema(extra_fields_plan)

    def test_validate_schema_async_behavior(self, planner):
        # Since the method does not involve any async operations, this test is not applicable.
        pass

# Note: Replace `your_module` with the actual module name where `LLMPlanner` and `PLAN_SCHEMA` are defined.
# The tests assume that `PLAN_SCHEMA` is correctly defined and that `LLMPlanner` has a method `_validate_schema`.