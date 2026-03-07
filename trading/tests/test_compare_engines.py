import pytest
from unittest.mock import patch
import os
import pandas as pd
from prettytable import PrettyTable

def mock_backtest_v2(*args, **kwargs):
    return {
        'stats': {
            'n_trades': 10,
            'win_rate': 0.6,
            'profit_factor': 2.5,
            'sharpe': 1.2,
            'max_drawdown': -0.3,
            'expectancy': 1500,
            'avg_r_multiple': 1.8
        }
    }

def test_run_comparison_happy_path():
    with patch('trading.compare_engines.backtest_v2', side_effect=mock_backtest_v2):
        run_comparison()

def test_run_comparison_empty_data_files(caplog):
    with patch('os.path.exists', return_value=False):
        run_comparison()
    assert "Data files not found." in caplog.text

def test_run_comparison_invalid_bt_config():
    bt_cfg = BacktestConfig(
        initial_capital=10_000.0,
        risk_per_trade=-0.01,  # Invalid value
        commission_rate=0.0004,
        slippage_rate=0.0002
    )
    with patch('trading.compare_engines.backtest_v2', side_effect=mock_backtest_v2):
        run_comparison()