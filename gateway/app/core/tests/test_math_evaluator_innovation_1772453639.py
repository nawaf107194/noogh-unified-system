import pytest

from gateway.app.core.math_evaluator import MathEvaluator, visit_Constant
from ast import Constant

def test_visit_Constant_happy_path():
    evaluator = MathEvaluator()
    node_int = Constant(value=42)
    node_float = Constant(value=3.14)
    
    assert evaluator.visit_Constant(node_int) == 42
    assert evaluator.visit_Constant(node_float) == 3.14

def test_visit_Constant_edge_case_empty():
    evaluator = MathEvaluator()
    node_empty = Constant(value=None)
    
    result = evaluator.visit_Constant(node_empty)
    assert result is None or isinstance(result, (int, float))

def test_visit_Constant_error_case_invalid_input():
    evaluator = MathEvaluator()
    node_str = Constant(value="hello")
    
    with pytest.raises(ValueError) as exc_info:
        evaluator.visit_Constant(node_str)
    assert str(exc_info.value) == "Unsupported constant: hello"