import pytest
from typing import Dict

class AdversarialThinkingModule:
    def __init__(self):
        self.risk_factors = ['factor1', 'factor2']
        self.impact_matrix = {'factor1': 2.0, 'factor2': 3.0}

    def assess_risks(self, trade_info: Dict) -> float:
        risk_score = 0.0
        for factor in self.risk_factors:
            if factor in trade_info:
                risk_score += self.impact_matrix.get(factor, 0.0) * trade_info[factor]
        return risk_score

@pytest.fixture
def module():
    return AdversarialThinkingModule()

def test_assess_risks_happy_path(module):
    trade_info = {'factor1': 5, 'factor2': 3}
    assert module.assess_risks(trade_info) == (5 * 2.0 + 3 * 3.0)

def test_assess_risks_empty_trade_info(module):
    trade_info = {}
    assert module.assess_risks(trade_info) == 0.0

def test_assess_risks_none_trade_info(module):
    assert module.assess_risks(None) is None

def test_assess_risks_boundary_values(module):
    trade_info = {'factor1': 1, 'factor2': 1}
    assert module.assess_risks(trade_info) == (1 * 2.0 + 1 * 3.0)

def test_assess_risks_missing_factors(module):
    trade_info = {'factor3': 7}
    assert module.assess_risks(trade_info) == 0.0