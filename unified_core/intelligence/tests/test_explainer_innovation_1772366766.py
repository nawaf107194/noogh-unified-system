import pytest

from unified_core.intelligence.explainer import Explainer, _simplify

@pytest.fixture
def explainer():
    return Explainer()

def test_simplify_happy_path(explainer):
    explanation = {
        'summary': 'The system detected a potential issue.',
        'reasoning': 'Some reasoning',
        'next_steps': 'Take action X'
    }
    result = _simplify(explanation)
    assert result == {
        'summary': 'The system detected a potential issue.',
        'reasoning': 'We looked at the situation and picked the safest path.',
        'next_steps': 'Take action X'
    }

def test_simplify_empty_input(explainer):
    explanation = {}
    result = _simplify(explanation)
    assert result == {
        'summary': None,
        'reasoning': 'We looked at the situation and picked the safest path.',
        'next_steps': None
    }

def test_simplify_none_input(explainer):
    explanation = None
    result = _simplify(explanation)
    assert result == {
        'summary': None,
        'reasoning': 'We looked at the situation and picked the safest path.',
        'next_steps': None
    }

def test_simplify_invalid_keys(explainer):
    explanation = {
        'other_key': 'Some value'
    }
    result = _simplify(explanation)
    assert result == {
        'summary': None,
        'reasoning': 'We looked at the situation and picked the safest path.',
        'next_steps': None
    }

def test_simplify_missing_keys(explainer):
    explanation = {}
    result = _simplify(explanation)
    assert result == {
        'summary': None,
        'reasoning': 'We looked at the situation and picked the safest path.',
        'next_steps': None
    }