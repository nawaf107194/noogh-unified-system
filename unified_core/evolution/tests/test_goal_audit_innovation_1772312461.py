import pytest

class MockGoalAudit:
    def __init__(self):
        self.type_stats = {
            "goal_type1": {"count": 10},
            "goal_type2": {"count": 3},
            "goal_type3": {"count": 8}
        }
    
    def get_type_performance(self, goal_type):
        return {
            "success_rate": 0.9,
            "avg_roi": 1.5
        }

@pytest.fixture
def goal_audit():
    return MockGoalAudit()

def test_identify_top_performers_happy_path(goal_audit):
    expected = [
        ("goal_type1", {
            "reason": "high_performance",
            "success_rate": 0.9,
            "avg_roi": 1.5,
            "suggested_weight": 1.5
        })
    ]
    assert goal_audit.identify_top_performers() == expected

def test_identify_top_performers_empty_stats(goal_audit):
    goal_audit.type_stats = {}
    assert goal_audit.identify_top_performers() == []

def test_identify_top_performers_min_samples_not_met(goal_audit):
    goal_audit.type_stats["goal_type1"]["count"] = 4
    assert goal_audit.identify_top_performers() == []

def test_identify_top_performers_performance_criteria_not_met(goal_audit):
    goal_audit.get_type_performance = lambda _: {"success_rate": 0.7, "avg_roi": 1.2}
    assert goal_audit.identify_top_performers() == []