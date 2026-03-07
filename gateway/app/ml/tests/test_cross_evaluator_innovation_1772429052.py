import pytest

class MockCrossEvaluator:
    def __init__(self):
        pass

    @staticmethod
    def _extract_domain_score(res: Any) -> float:
        """Heuristic to pull a 0-10 score from training results."""
        if not res:
            return 0.0
        # Try to find accuracy in improvement report
        try:
            # Look into the nested structure of our distillation results
            eval_data = res.get("details", [])[0].get("eval", {})
            return eval_data.get("optimized", {}).get("accuracy", 5.5)
        except Exception:
            return 0.0

def test_extract_domain_score_happy_path():
    evaluator = MockCrossEvaluator()
    result = {"details": [{"eval": {"optimized": {"accuracy": 7.8}}}], "other_key": "value"}
    assert evaluator._extract_domain_score(result) == 7.8

def test_extract_domain_score_empty_input():
    evaluator = MockCrossEvaluator()
    result = {}
    assert evaluator._extract_domain_score(result) == 0.0

def test_extract_domain_score_none_input():
    evaluator = MockCrossEvaluator()
    assert evaluator._extract_domain_score(None) == 0.0

def test_extract_domain_score_boundary_value():
    evaluator = MockCrossEvaluator()
    result = {"details": [{"eval": {"optimized": {"accuracy": 10}}}], "other_key": "value"}
    assert evaluator._extract_domain_score(result) == 10.0
    result = {"details": [{"eval": {"optimized": {"accuracy": 0}}}], "other_key": "value"}
    assert evaluator._extract_domain_score(result) == 0.0

def test_extract_domain_score_missing_accuracy():
    evaluator = MockCrossEvaluator()
    result = {"details": [{"eval": {}}], "other_key": "value"}
    assert evaluator._extract_domain_score(result) == 5.5