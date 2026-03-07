import pytest
import os
import pandas as pd
from backtesting.config import BacktestConfig, RiskConfig
from trading.signal_engine_v3_liquidity_trap import SignalEngineV3_LiquidityTrap
from trading.indicator_config import IndicatorConfig
from trading.score_weights import ScoreWeights
from trading.position_size_from_risk import position_size_from_risk

@pytest.fixture
def test_data():
    symbol = "BTCUSDT"
    data_dir = os.path.join(os.getcwd(), "tests", "data")
    micro_path = os.path.join(data_dir, f"{symbol}_5m_3M.parquet")
    macro_path = os.path.join(data_dir, f"{symbol}_1h_3M.parquet")

    df_micro = pd.read_parquet(micro_path)
    df_macro = pd.read_parquet(macro_path)

    bt = BacktestConfig(
        initial_capital=10_000.0,
        risk_per_trade=0.01,
        commission_rate=0.0004,
        slippage_rate=0.0002
    )

    risk_cfg = RiskConfig(min_rrr=1.0, tp2_mult=float('nan'), tp3_mult=float('nan'))

    return df_micro, df_macro, bt, risk_cfg

def prepare_aligned_data(df_micro, df_macro):
    # Mock implementation of prepare_aligned_data
    # This should be replaced with the actual implementation in your test environment
    return pd.concat([df_micro, df_macro], axis=1)

@pytest.mark.parametrize("input_df_micro, input_df_macro, bt, risk_cfg", [test_data()])
def test_debug_signal_rejections(input_df_micro, input_df_macro, bt, risk_cfg):
    aligned = prepare_aligned_data(input_df_micro, input_df_macro)

    rejections = debug_signal_rejections()

    # Assert rejection counts
    assert 'no_signal' in rejections
    assert 'no_stop_loss' in rejections
    assert 'invalid_sl' in rejections
    assert 'no_tp1' in rejections
    assert 'qty_zero' in rejections
    assert 'accepted' in rejections

    # Assert total bars analyzed
    assert len(aligned) - 2 == rejections['no_signal'] + rejections['no_stop_loss'] + rejections['invalid_sl'] + rejections['no_tp1'] + rejections['qty_zero'] + rejections['accepted']

def test_debug_signal_rejections_empty_input():
    symbol = "BTCUSDT"
    data_dir = os.path.join(os.getcwd(), "tests", "data")
    micro_path = os.path.join(data_dir, f"{symbol}_5m_3M.parquet")
    macro_path = os.path.join(data_dir, f"{symbol}_1h_3M.parquet")

    df_micro = pd.DataFrame()
    df_macro = pd.DataFrame()

    bt = BacktestConfig(
        initial_capital=10_000.0,
        risk_per_trade=0.01,
        commission_rate=0.0004,
        slippage_rate=0.0002
    )

    risk_cfg = RiskConfig(min_rrr=1.0, tp2_mult=float('nan'), tp3_mult=float('nan'))

    aligned = prepare_aligned_data(df_micro, df_macro)

    rejections = debug_signal_rejections()

    # Assert rejection counts for empty input
    assert rejections['no_signal'] == len(aligned) - 2
    assert rejections['no_stop_loss'] == 0
    assert rejections['invalid_sl'] == 0
    assert rejections['no_tp1'] == 0
    assert rejections['qty_zero'] == 0
    assert rejections['accepted'] == 0

def test_debug_signal_rejections_invalid_inputs():
    symbol = "BTCUSDT"
    data_dir = os.path.join(os.getcwd(), "tests", "data")
    micro_path = os.path.join(data_dir, f"{symbol}_5m_3M.parquet")
    macro_path = os.path.join(data_dir, f"{symbol}_1h_3M.parquet")

    df_micro = pd.read_parquet(micro_path)
    df_macro = pd.DataFrame()

    bt = BacktestConfig(
        initial_capital=10_000.0,
        risk_per_trade=0.01,
        commission_rate=0.0004,
        slippage_rate=0.0002
    )

    risk_cfg = RiskConfig(min_rrr=1.0, tp2_mult=float('nan'), tp3_mult=float('nan'))

    aligned = prepare_aligned_data(df_micro, df_macro)

    with pytest.raises(ValueError):
        debug_signal_rejections()