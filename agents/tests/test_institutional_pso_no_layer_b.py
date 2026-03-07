import numpy as np
from typing import Tuple

class InstitutionalPSO:
    def __init__(self, weights: np.ndarray, gate_atr: float, threshold: float):
        self.weights = weights
        self.gate_atr = gate_atr
        self.threshold = threshold

    def __call__(self, x: np.ndarray) -> Tuple[bool, float]:
        if x[0] > self.gate_atr:
            return False, 0.0
        score = float(np.dot(self.weights, x))
        return (score > self.threshold), score

@pytest.fixture
def institutional_pso():
    weights = np.array([1.0, 2.0, 3.0])
    gate_atr = 5.0
    threshold = 10.0
    return InstitutionalPSO(weights, gate_atr, threshold)

def test_happy_path(institutional_pso):
    x = np.array([4.0, 2.0, 3.0])
    expected_result = (False, 0.0)
    assert institutional_pso(x) == expected_result

    x = np.array([1.0, 2.0, 3.0])
    expected_result = (True, 16.0)
    assert institutional_pso(x) == expected_result

def test_edge_cases(institutional_pso):
    x_empty = np.array([])
    with pytest.raises(ValueError) as excinfo:
        institutional_pso(x_empty)
    assert "x must be a non-empty numpy array" in str(excinfo.value)

    x_none = None
    with pytest.raises(TypeError) as excinfo:
        institutional_pso(x_none)
    assert "x must be a numpy array" in str(excinfo.value)

    x_boundary = np.array([5.0, 2.0, 3.0])
    expected_result = (False, 0.0)
    assert institutional_pso(x_boundary) == expected_result

def test_error_cases(institutional_pso):
    weights_invalid_type = "not an array"
    with pytest.raises(TypeError) as excinfo:
        InstitutionalPSO(weights_invalid_type, 5.0, 10.0)
    assert "weights must be a numpy array" in str(excinfo.value)

    gate_atr_invalid_type = "not a number"
    with pytest.raises(TypeError) as excinfo:
        InstitutionalPSO(np.array([1.0, 2.0, 3.0]), gate_atr_invalid_type, 10.0)
    assert "gate_atr must be a float" in str(excinfo.value)

    threshold_invalid_type = "not a number"
    with pytest.raises(TypeError) as excinfo:
        InstitutionalPSO(np.array([1.0, 2.0, 3.0]), 5.0, threshold_invalid_type)
    assert "threshold must be a float" in str(excinfo.value)

def test_async_behavior(institutional_pso):
    # Since the function is not asynchronous and does not have any delay,
    # this test case is more of a placeholder.
    pass