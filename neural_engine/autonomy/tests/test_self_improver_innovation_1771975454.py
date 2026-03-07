import pytest

class MockSelfImprover:
    def __init__(self, proposals=None, plans=None):
        self.proposals = proposals or {}
        self.plans = plans or []

    def _group_by_category(self):
        return {}

    def _group_by_risk(self):
        return {}

def test_get_improvement_summary_happy_path():
    # Happy path: Normal inputs
    proposals = {
        'p1': {'blocked': False},
        'p2': {'blocked': True},
        'p3': {'blocked': False}
    }
    plans = ['plan1', 'plan2']
    improver = MockSelfImprover(proposals, plans)
    
    result = improver.get_improvement_summary()
    
    assert result == {
        "total_proposals": 3,
        "blocked": 1,
        "pending_review": 2,
        "by_category": {},
        "by_risk": {},
        "total_plans": 2
    }

def test_get_improvement_summary_edge_case_empty():
    # Edge case: Empty inputs
    improver = MockSelfImprover()
    
    result = improver.get_improvement_summary()
    
    assert result == {
        "total_proposals": 0,
        "blocked": 0,
        "pending_review": 0,
        "by_category": {},
        "by_risk": {},
        "total_plans": 0
    }

def test_get_improvement_summary_edge_case_none():
    # Edge case: None inputs
    improver = MockSelfImprover(proposals=None, plans=None)
    
    result = improver.get_improvement_summary()
    
    assert result == {
        "total_proposals": 0,
        "blocked": 0,
        "pending_review": 0,
        "by_category": {},
        "by_risk": {},
        "total_plans": 0
    }

def test_get_improvement_summary_edge_case_single_plan():
    # Edge case: Single plan
    plans = ['single_plan']
    improver = MockSelfImprover(plans=plans)
    
    result = improver.get_improvement_summary()
    
    assert result == {
        "total_proposals": 0,
        "blocked": 0,
        "pending_review": 0,
        "by_category": {},
        "by_risk": {},
        "total_plans": 1
    }