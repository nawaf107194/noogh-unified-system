import pytest

class TestPlanningEngine:

    @pytest.fixture
    def planning_engine(self):
        from unified_core.core.planning_engine import PlanningEngine
        return PlanningEngine()

    def test_get_plan_status_normal_input(self, planning_engine):
        # Arrange
        planning_engine._active_plans = {
            '123': MockPlan('123', 'in_progress')
        }
        
        # Act
        result = planning_engine.get_plan_status('123')
        
        # Assert
        assert result == {'plan_id': '123', 'status': 'in_progress'}

    def test_get_plan_status_empty_input(self, planning_engine):
        # Arrange
        planning_engine._active_plans = {}
        planning_engine._plan_history = []
        
        # Act
        result = planning_engine.get_plan_status('')
        
        # Assert
        assert result is None

    def test_get_plan_status_none_input(self, planning_engine):
        # Arrange
        planning_engine._active_plans = {}
        planning_engine._plan_history = []
        
        # Act
        result = planning_engine.get_plan_status(None)
        
        # Assert
        assert result is None

    def test_get_plan_status_not_found_in_active(self, planning_engine):
        # Arrange
        planning_engine._active_plans = {}
        planning_engine._plan_history = [
            MockPlan('456', 'completed'),
            MockPlan('789', 'cancelled')
        ]
        
        # Act
        result = planning_engine.get_plan_status('123')
        
        # Assert
        assert result == {'plan_id': '456', 'status': 'completed'}

    def test_get_plan_status_not_found_in_history(self, planning_engine):
        # Arrange
        planning_engine._active_plans = {}
        planning_engine._plan_history = []
        
        # Act
        result = planning_engine.get_plan_status('123')
        
        # Assert
        assert result is None

class MockPlan:
    def __init__(self, plan_id: str, status: str):
        self.plan_id = plan_id
        self.status = status
    
    def to_dict(self):
        return {'plan_id': self.plan_id, 'status': self.status}