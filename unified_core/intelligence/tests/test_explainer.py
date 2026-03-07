import pytest

from unified_core.intelligence.explainer import Explainer, Decision

def test_explain_confidence_happy_path():
    explainer = Explainer()
    decision = Decision(
        confidence=0.95,
        evidence_quality=0.9,
        strategy_success_rate=0.85,
        risk_score=25
    )
    result = explainer._explain_confidence(decision)
    assert result == {
        'level': 0.95,
        'factors': ['✓ Strong evidence', '✓ Proven strategy', '✓ Low risk'],
        'interpretation': explainer._interpret_confidence(0.95)
    }

def test_explain_confidence_edge_cases():
    explainer = Explainer()
    decision_empty = Decision(
        confidence=None,
        evidence_quality=None,
        strategy_success_rate=None,
        risk_score=None
    )
    result_empty = explainer._explain_confidence(decision_empty)
    assert result_empty == {
        'level': None,
        'factors': [],
        'interpretation': None
    }

    decision_boundary = Decision(
        confidence=0.75,
        evidence_quality=0.8,
        strategy_success_rate=0.7,
        risk_score=30
    )
    result_boundary = explainer._explain_confidence(decision_boundary)
    assert result_boundary == {
        'level': 0.75,
        'factors': ['⚠ Weak evidence', '✓ Proven strategy', '⚠ High risk'],
        'interpretation': explainer._interpret_confidence(0.75)
    }

def test_explain_confidence_error_cases():
    explainer = Explainer()
    decision_invalid_evidence = Decision(
        confidence=0.9,
        evidence_quality=-1,
        strategy_success_rate=0.85,
        risk_score=25
    )
    result_invalid_evidence = explainer._explain_confidence(decision_invalid_evidence)
    assert result_invalid_evidence == {
        'level': 0.9,
        'factors': ['⚠ Invalid evidence', '✓ Proven strategy', '✓ Low risk'],
        'interpretation': explainer._interpret_confidence(0.9)
    }

    decision_invalid_strategy = Decision(
        confidence=0.9,
        evidence_quality=0.8,
        strategy_success_rate=-1,
        risk_score=25
    )
    result_invalid_strategy = explainer._explain_confidence(decision_invalid_strategy)
    assert result_invalid_strategy == {
        'level': 0.9,
        'factors': ['⚠ Weak evidence', '⚠ Invalid strategy', '✓ Low risk'],
        'interpretation': explainer._interpret_confidence(0.9)
    }

    decision_invalid_risk = Decision(
        confidence=0.9,
        evidence_quality=0.8,
        strategy_success_rate=0.85,
        risk_score=-1
    )
    result_invalid_risk = explainer._explain_confidence(decision_invalid_risk)
    assert result_invalid_risk == {
        'level': 0.9,
        'factors': ['⚠ Weak evidence', '✓ Proven strategy', '⚠ Invalid risk'],
        'interpretation': explainer._interpret_confidence(0.9)
    }