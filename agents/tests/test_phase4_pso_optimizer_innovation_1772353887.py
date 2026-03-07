import pytest
from agents.phase4_pso_optimizer import fitness, Policy

def test_happy_path():
    # Mock policy with normal values
    mock_policy = Policy()
    mock_policy.evaluate.return_value = {
        'n_trades': 20,
        'pf': 2.5,
        'max_dd': 25,
        'total_r': 100
    }

    result_robust = fitness(mock_policy, "robust")
    assert result_robust > 0

    result_aggressive = fitness(mock_policy, "aggressive")
    assert result_aggressive == score_single(result_robust)

def test_edge_cases():
    # Mock policy with edge cases
    mock_policy_edge = Policy()
    mock_policy_edge.evaluate.return_value = {
        'n_trades': 5,
        'pf': 1.0,
        'max_dd': 31,
        'total_r': -100
    }

    result_robust = fitness(mock_policy_edge, "robust")
    assert result_robust == 0

    result_aggressive = fitness(mock_policy_edge, "aggressive")
    assert result_aggressive == 0

def test_error_cases():
    # Mock policy with invalid inputs (should not happen in normal use)
    mock_policy_invalid = Policy()
    mock_policy_invalid.evaluate.return_value = None

    result_robust = fitness(mock_policy_invalid, "robust")
    assert result_robust == 0

    result_aggressive = fitness(mock_policy_invalid, "aggressive")
    assert result_aggressive == 0

def test_async_behavior():
    # This function does not exhibit async behavior, so no async tests are needed
    pass

# Helper function to calculate score_single for testing purposes
def score_single(res):
    pf_norm = min(res['pf'], 3.0) / 3.0
    exp = res['total_r'] / res['n_trades'] if res['n_trades'] > 0 else 0
    exp_norm = np.tanh(exp * 2)
    dd_penalty = np.exp(-res['max_dd'] / 10)
    n_bonus = min(res['n_trades'] / 50, 1.0)
    return (pf_norm * 0.4 + exp_norm * 0.3 + dd_penalty * 0.2 + n_bonus * 0.1)

# Import numpy for the tanh function
import numpy as np