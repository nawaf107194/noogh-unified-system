import pytest

from gateway.app.ml.cross_evaluator import CrossEvaluator, ModelEvaluator


@pytest.fixture
def cross_evaluator():
    return CrossEvaluator()


def test_happy_path(cross_evaluator):
    assert isinstance(cross_evaluator.base_evaluator, ModelEvaluator)
    assert cross_evaluator.weights == {
        "computer_science": 0.25,
        "artificial_intelligence": 0.30,
        "programming": 0.25,
        "mathematics": 0.20,
    }


def test_edge_case_empty_weights(cross_evaluator):
    cross_evaluator.weights = {}
    assert isinstance(cross_evaluator.base_evaluator, ModelEvaluator)
    assert cross_evaluator.weights == {}


def test_edge_case_none_weights(cross_evaluator):
    cross_evaluator.weights = None
    assert isinstance(cross_evaluator.base_evaluator, ModelEvaluator)
    assert cross_evaluator.weights is None


def test_error_case_invalid_weights_type(cross_evaluator):
    with pytest.raises(TypeError) as exc_info:
        cross_evaluator.weights = "invalid"
    assert str(exc_info.value) == "Weights must be a dictionary"


def test_error_case_invalid_weights_value_type(cross_evaluator):
    with pytest.raises(ValueError) as exc_info:
        cross_evaluator.weights = {
            "computer_science": "0.25",
            "artificial_intelligence": 0.30,
            "programming": 0.25,
            "mathematics": 0.20,
        }
    assert str(exc_info.value) == "Weights must be a dictionary with numeric values"


def test_error_case_weights_sum_not_one(cross_evaluator):
    with pytest.raises(ValueError) as exc_info:
        cross_evaluator.weights = {
            "computer_science": 0.25,
            "artificial_intelligence": 0.30,
            "programming": 0.15,
            "mathematics": 0.20,
        }
    assert str(exc_info.value) == "Sum of weights must be equal to 1"