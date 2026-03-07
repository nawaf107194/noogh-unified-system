import pytest

from unified_core.core.planning_engine import PlanningEngine, SubTask

class TestPlanningEngine:

    @pytest.fixture
    def planning_engine(self):
        return PlanningEngine()

    def test_generic_decomposition_happy_path(self, planning_engine: PlanningEngine):
        goal = "update_system"
        expected_subtasks = [
            SubTask("analyze", "Analyze requirements for: update_system", "linux", task_type="system_update"),
            SubTask("execute", "Execute actions for: update_system", "linux", task_type="disk_usage"),
            SubTask("verify", "Verify completion of: update_system", "qa", task_type="regression_detected")
        ]
        assert planning_engine._generic_decomposition(goal) == expected_subtasks

    def test_generic_decomposition_edge_cases(self, planning_engine: PlanningEngine):
        goal = ""
        with pytest.raises(ValueError):
            planning_engine._generic_decomposition(goal)

        goal = None
        with pytest.raises(TypeError):
            planning_engine._generic_decomposition(goal)

    def test_generic_decomposition_error_cases(self, planning_engine: PlanningEngine):
        # Assuming _gen_task_id method can raise ValueError for invalid inputs
        with pytest.raises(ValueError):
            planning_engine._gen_task_id("")

    @pytest.mark.asyncio
    async def test_generic_decomposition_async_behavior(self, planning_engine: PlanningEngine):
        goal = "update_system"
        subtasks = await planning_engine._generic_decomposition(goal)
        assert len(subtasks) == 3