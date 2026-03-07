import pytest

class MockSelfImprover:
    def __init__(self):
        self.proposals = {}
        self.plans = {}

    def _group_by_category(self):
        return {}

    def _group_by_risk(self):
        return {}

def test_get_improvement_summary_happy_path():
    self_improver = MockSelfImprover()
    self_improver.proposals = {
        '1': {'blocked': False},
        '2': {'blocked': True}
    }
    self_improver.plans = ['plan1', 'plan2']
    expected_output = {
        "total_proposals": 2,
        "blocked": 1,
        "pending_review": 1,
        "by_category": {},
        "by_risk": {},
        "total_plans": 2
    }
    assert self_improver.get_improvement_summary() == expected_output

def test_get_improvement_summary_empty_proposals():
    self_improver = MockSelfImprover()
    self_improver.proposals = {}
    self_improver.plans = []
    expected_output = {
        "total_proposals": 0,
        "blocked": 0,
        "pending_review": 0,
        "by_category": {},
        "by_risk": {},
        "total_plans": 0
    }
    assert self_improver.get_improvement_summary() == expected_output

def test_get_improvement_summary_none_values():
    self_improver = MockSelfImprover()
    self_improver.proposals = None
    self_improver.plans = None
    expected_output = {
        "total_proposals": 0,
        "blocked": 0,
        "pending_review": 0,
        "by_category": {},
        "by_risk": {},
        "total_plans": 0
    }
    assert self_improver.get_improvement_summary() == expected_output

def test_get_improvement_summary_empty_plans():
    self_improver = MockSelfImprover()
    self_improver.proposals = {
        '1': {'blocked': False},
        '2': {'blocked': True}
    }
    self.improver.plans = []
    expected_output = {
        "total_proposals": 2,
        "blocked": 1,
        "pending_review": 1,
        "by_category": {},
        "by_risk": {},
        "total_plans": 0
    }
    assert self_improver.get_improvement_summary() == expected_output

def test_get_improvement_summary_boundary_values():
    self_improver = MockSelfImprover()
    self_improver.proposals = {
        '1': {'blocked': False},
        '2': {'blocked': False},
        '3': {'blocked': True}
    }
    self.improver.plans = ['plan1']
    expected_output = {
        "total_proposals": 3,
        "blocked": 1,
        "pending_review": 2,
        "by_category": {},
        "by_risk": {},
        "total_plans": 1
    }
    assert self_improver.get_improvement_summary() == expected_output