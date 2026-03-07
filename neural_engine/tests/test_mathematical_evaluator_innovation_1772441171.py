import pytest

from neural_engine.mathematical_evaluator import MathematicalEvaluator

def test_check_dimensional_consistency_happy_path():
    evaluator = MathematicalEvaluator()
    response = {
        "steps": [
            {"verification": "Check the units in the equation"}
        ],
        "raw_response": "The result is 10 meters."
    }
    result = evaluator._check_dimensional_consistency(response)
    assert result == {"consistent": True, "issues": []}

def test_check_dimensional_consistency_no_steps():
    evaluator = MathematicalEvaluator()
    response = {
        "steps": [],
        "raw_response": "The result is 10 meters."
    }
    result = evaluator._check_dimensional_consistency(response)
    assert result == {"consistent": False, "issues": ["Missing dimensional verification for query with units"]}

def test_check_dimensional_consistency_no_units():
    evaluator = MathematicalEvaluator()
    response = {
        "steps": [
            {"verification": "Check the units in the equation"}
        ],
        "raw_response": "The result is 10"
    }
    result = evaluator._check_dimensional_consistency(response)
    assert result == {"consistent": True, "issues": []}

def test_check_dimensional_consistency_empty_raw_response():
    evaluator = MathematicalEvaluator()
    response = {
        "steps": [
            {"verification": "Check the units in the equation"}
        ],
        "raw_response": ""
    }
    result = evaluator._check_dimensional_consistency(response)
    assert result == {"consistent": False, "issues": ["Missing dimensional verification for query with units"]}

def test_check_dimensional_consistency_none_steps():
    evaluator = MathematicalEvaluator()
    response = {
        "steps": None,
        "raw_response": "The result is 10 meters."
    }
    result = evaluator._check_dimensional_consistency(response)
    assert result == {"consistent": False, "issues": ["Missing dimensional verification for query with units"]}

def test_check_dimensional_consistency_none_raw_response():
    evaluator = MathematicalEvaluator()
    response = {
        "steps": [
            {"verification": "Check the units in the equation"}
        ],
        "raw_response": None
    }
    result = evaluator._check_dimensional_consistency(response)
    assert result == {"consistent": False, "issues": ["Missing dimensional verification for query with units"]}

def test_check_dimensional_consistency_invalid_input():
    evaluator = MathematicalEvaluator()
    response = "Not a dictionary"
    result = evaluator._check_dimensional_consistency(response)
    assert result is None