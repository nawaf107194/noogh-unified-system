import pytest
from unified_core.orchestration.llm_planner import _validate_schema, PlanBuildError

@pytest.fixture
def plan_schema():
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "steps": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["name", "steps"]
    }

@pytest.mark.parametrize("plan, expected_error", [
    ({"name": "Test Plan", "steps": ["Step 1", "Step 2"]}, None),
    ({}, "Schema validation failed: 'name' is a required property"),
    (None, "Schema validation failed: None is not an object"),
    ({"name": "Test Plan"}, "Schema validation failed: 'steps' is a required property"),
    ({"name": "Test Plan", "steps": 123}, "Schema validation failed: 'steps' must be array")
])
def test_validate_schema(plan, expected_error, plan_schema):
    with pytest.raises(PlanBuildError) if expected_error else nullcontext():
        _validate_schema(plan)