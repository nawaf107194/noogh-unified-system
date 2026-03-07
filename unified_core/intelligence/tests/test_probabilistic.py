import pytest
from unified_core.intelligence.probabilistic import ProbabilisticOption, Outcome

def test_decision_under_uncertainty_happy_path():
    options = [
        ProbabilisticOption(
            name="OptionA",
            possible_outcomes=[
                Outcome("Outcome1", 0.5, 10),
                Outcome("Outcome2", 0.5, 20)
            ]
        ),
        ProbabilisticOption(
            name="OptionB",
            possible_outcomes=[
                Outcome("Outcome3", 1.0, -5)
            ]
        )
    ]

    result = decision_under_uncertainty(options)
    assert 'best_choice' in result
    assert result['best_choice'] == "OptionA"
    assert len(result['evaluations']) == 2

def test_decision_under_uncertainty_empty_options():
    options = []
    
    result = decision_under_uncertainty(options)
    assert result == {}

def test_decision_under_uncertainty_none_options():
    result = decision_under_uncertainty(None)
    assert result == {}

def test_decision_under_uncertainty_single_option():
    options = [
        ProbabilisticOption(
            name="SingleOption",
            possible_outcomes=[
                Outcome("Outcome1", 1.0, 30)
            ]
        )
    ]

    result = decision_under_uncertainty(options)
    assert 'best_choice' in result
    assert result['best_choice'] == "SingleOption"
    assert len(result['evaluations']) == 1

def test_decision_under_uncertainty_normalized_probabilities():
    options = [
        ProbabilisticOption(
            name="OptionA",
            possible_outcomes=[
                Outcome("Outcome1", 0.3, 5),
                Outcome("Outcome2", 0.7, 25)
            ]
        )
    ]

    result = decision_under_uncertainty(options)
    assert 'best_choice' in result
    assert result['best_choice'] == "OptionA"
    assert len(result['evaluations']) == 1

def test_decision_under_uncertainty_risk_aversion():
    options = [
        ProbabilisticOption(
            name="OptionA",
            possible_outcomes=[
                Outcome("Outcome1", 0.5, 10),
                Outcome("Outcome2", 0.5, 20)
            ]
        )
    ]

    result_default_risk_aversion = decision_under_uncertainty(options)
    result_high_risk_aversion = decision_under_uncertainty(options, risk_aversion=2.0)

    assert result_high_risk_aversion['evaluations'][0]['risk_adjusted_score'] < result_default_risk_aversion['evaluations'][0]['risk_adjusted_score']

def test_decision_under_uncertainty_large_variance():
    options = [
        ProbabilisticOption(
            name="OptionA",
            possible_outcomes=[
                Outcome("Outcome1", 1.0, -10)
            ]
        )
    ]

    result = decision_under_uncertainty(options)

    assert 'best_choice' in result
    assert result['best_choice'] == "None"  # Assuming OptionA is not chosen due to its large negative utility

def test_decision_under_uncertainty_catastrophic_risk():
    options = [
        ProbabilisticOption(
            name="OptionA",
            possible_outcomes=[
                Outcome("Outcome1", 0.5, 10),
                Outcome("Outcome2", 0.5, -100)
            ]
        ),
        ProbabilisticOption(
            name="OptionB",
            possible_outcomes=[
                Outcome("Outcome3", 1.0, 5)
            ]
        )
    ]

    result = decision_under_uncertainty(options)

    assert 'best_choice' in result
    assert result['best_choice'] == "OptionB"  # Assuming OptionA is not chosen due to high catastrophic risk

# Add async tests if the function has any async behavior