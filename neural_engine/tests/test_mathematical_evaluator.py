import pytest
from neural_engine.mathematical_evaluator import MathematicalEvaluator

def test_check_formula_derivation_happy_path():
    evaluator = MathematicalEvaluator()
    response = {
        "raw_response": "The determinant formula is derived as..."
    }
    result = evaluator._check_formula_derivation(response)
    assert result == {"all_derived": True, "underived": []}

def test_check_formula_derivation_no_keywords():
    evaluator = MathematicalEvaluator()
    response = {
        "raw_response": "This is a simple calculation."
    }
    result = evaluator._check_formula_derivation(response)
    assert result == {"all_derived": True, "underived": []}

def test_check_formula_derivation_with_keywords_no_derivation():
    evaluator = MathematicalEvaluator()
    response = {
        "raw_response": "The determinant formula is not derived here."
    }
    result = evaluator._check_formula_derivation(response)
    assert result == {"all_derived": False, "underived": ["determinant formula"]}

def test_check_formula_derivation_with_keywords_and_derivation():
    evaluator = MathematicalEvaluator()
    response = {
        "raw_response": "The determinant formula is derived by following these steps..."
    }
    result = evaluator._check_formula_derivation(response)
    assert result == {"all_derived": True, "underived": []}

def test_check_formula_derivation_empty_response():
    evaluator = MathematicalEvaluator()
    response = {
        "raw_response": ""
    }
    result = evaluator._check_formula_derivation(response)
    assert result == {"all_derived": True, "underived": []}

def test_check_formula_derivation_none_response():
    evaluator = MathematicalEvaluator()
    response = None
    result = evaluator._check_formula_derivation(response)
    assert result == {"all_derived": True, "underived": []}

def test_check_formula_derivation_invalid_input_type():
    evaluator = MathematicalEvaluator()
    with pytest.raises(TypeError):
        evaluator._check_formula_derivation("This is not a dict")