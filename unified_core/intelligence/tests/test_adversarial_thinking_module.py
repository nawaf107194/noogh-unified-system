import pytest

@pytest.fixture
def adversarial_thinking_module():
    from unified_core.intelligence.adversarial_thinking_module import AdversarialThinkingModule
    return AdversarialThinkingModule()

def test_evaluate_trade_happy_path(adversarial_thinking_module):
    trade_info = {
        'risk_factors': [0.1, 0.2, 0.3],
        'potential_gain': 100
    }
    result = adversarial_thinking_module.evaluate_trade(trade_info)
    assert result is True

def test_evaluate_trade_edge_case_empty_trade_info(adversarial_thinking_module):
    trade_info = {}
    result = adversarial_thinking_module.evaluate_trade(trade_info)
    assert result is False

def test_evaluate_trade_edge_case_none_trade_info(adversarial_thinking_module):
    result = adversarial_thinking_module.evaluate_trade(None)
    assert result is False

def test_evaluate_trade_error_case_invalid_risk_score(adversarial_thinking_module):
    trade_info = {
        'risk_factors': [-0.1],
        'potential_gain': 100
    }
    with pytest.raises(ValueError) as excinfo:
        adversarial_thinking_module.evaluate_trade(trade_info)
    assert "Risk score cannot be negative" in str(excinfo.value)

# Assuming assess_risks method raises ValueError for invalid risk scores
def test_assess_risks_error_case_invalid_risk_score(adversarial_thinking_module):
    with pytest.raises(ValueError) as excinfo:
        adversarial_thinking_module.assess_risks({'risk_factors': [-0.1]})
    assert "Risk score cannot be negative" in str(excinfo.value)