import pytest
import ast
import sys
from math_evaluator import MathEvaluator

def test_visit_expression_happy_path():
    # Test basic arithmetic expression
    node = ast.parse("1 + 2", mode="eval").body
    evaluator = MathEvaluator(node)
    assert evaluator.visit_Expression(node) == 3

def test_visit_expression_edge_case_min_int():
    # Test with smallest possible integer
    node = ast.parse(f"{sys.maxsize}", mode="eval").body
    evaluator = MathEvaluator(node)
    assert evaluator.visit_Expression(node) == sys.maxsize

def test_visit_expression_edge_case_max_int():
    # Test with largest possible integer
    node = ast.parse(f"{-sys.maxsize}", mode="eval").body
    evaluator = MathEvaluator(node)
    assert evaluator.visit_Expression(node) == -sys.maxsize

def test_visit_expression_edge_case_single_number():
    # Test with single number
    node = ast.parse("42", mode="eval").body
    evaluator = MathEvaluator(node)
    assert evaluator.visit_Expression(node) == 42

def test_visit_expression_error_case_invalid_node():
    # Test with invalid node type
    node = ast.parse("None", mode="eval").body
    evaluator = MathEvaluator(node)
    with pytest.raises(TypeError):
        evaluator.visit_Expression(node)