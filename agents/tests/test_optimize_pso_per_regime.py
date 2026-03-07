import pytest
from agents.optimize_pso_per_regime import Policy, fitness

class MockPolicy(Policy):
    def __init__(self, n_trades=0, pf=1.0, max_dd=0, total_r=0):
        self.n_trades = n_trades
        self.pf = pf
        self.max_dd = max_dd
        self.total_r = total_r

def test_happy_path():
    policy = MockPolicy(n_trades=10, pf=2.5, max_dd=15, total_r=100)
    train_data = [{"key": "value"}]
    val_data = [{"key": "value"}]
    result_robust = fitness(policy, train_data, val_data, mode="robust")
    result_aggressive = fitness(policy, train_data, val_data, mode="aggressive")
    assert result_robust > 0
    assert result_aggressive > 0

def test_edge_cases():
    policy_empty_train = MockPolicy(n_trades=10, pf=2.5, max_dd=15, total_r=100)
    train_data_empty = []
    val_data_empty = [{"key": "value"}]
    result_robust_empty_train = fitness(policy_empty_train, train_data_empty, val_data_empty, mode="robust")
    assert result_robust_empty_train == 0.0

    policy_empty_val = MockPolicy(n_trades=10, pf=2.5, max_dd=15, total_r=100)
    train_data_empty = [{"key": "value"}]
    val_data_empty = []
    result_robust_empty_val = fitness(policy_empty_val, train_data_empty, val_data_empty, mode="robust")
    assert result_robust_empty_val == 0.0

def test_kill_conditions():
    policy_low_trades = MockPolicy(n_trades=4, pf=2.5, max_dd=15, total_r=100)
    train_data = [{"key": "value"}]
    val_data = [{"key": "value"}]
    result_robust_low_trades = fitness(policy_low_trades, train_data, val_data, mode="robust")
    assert result_robust_low_trades == 0.0

    policy_low_pf = MockPolicy(n_trades=10, pf=1.0, max_dd=15, total_r=100)
    train_data = [{"key": "value"}]
    val_data = [{"key": "value"}]
    result_robust_low_pf = fitness(policy_low_pf, train_data, val_data, mode="robust")
    assert result_robust_low_pf == 0.0

    policy_high_max_dd = MockPolicy(n_trades=10, pf=2.5, max_dd=35, total_r=100)
    train_data = [{"key": "value"}]
    val_data = [{"key": "value"}]
    result_robust_high_max_dd = fitness(policy_high_max_dd, train_data, val_data, mode="robust")
    assert result_robust_high_max_dd == 0.0

def test_modes():
    policy = MockPolicy(n_trades=10, pf=2.5, max_dd=15, total_r=100)
    train_data = [{"key": "value"}]
    val_data = [{"key": "value"}]
    result_robust = fitness(policy, train_data, val_data, mode="robust")
    result_aggressive = fitness(policy, train_data, val_data, mode="aggressive")
    assert result_robust != result_aggressive