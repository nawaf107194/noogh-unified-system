import pytest
import os
from datetime import timedelta
from trading.temporal_analysis import run_temporal_analysis, SignalEngineV3_LiquidityTrap, BacktestConfig, RiskConfig
from trading.indicators import IndicatorConfig
from trading.scores import ScoreWeights
from trading.backtesting_v2 import backtest_v2

@pytest.fixture
def setup_data():
    # Setup mock data for testing
    symbol = "BTCUSDT"
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    micro_path = os.path.join(data_dir, f"{symbol}_5m_3M.parquet")
    macro_path = os.path.join(data_dir, f"{symbol}_1h_3M.parquet")

    # Create mock data (this should be replaced with actual data loading logic)
    df_micro = pd.DataFrame({
        'entry_time': pd.date_range(start='2023-01-01', periods=100, freq='5T'),
        'exit_time': pd.date_range(start='2023-01-01', periods=100, freq='5T') + timedelta(minutes=5),
        'pnl': [1, -1] * 50,
    })
    df_macro = pd.DataFrame()

    # Save mock data to files
    os.makedirs(data_dir, exist_ok=True)
    df_micro.to_parquet(micro_path)
    df_macro.to_parquet(macro_path)

    yield symbol, micro_path, macro_path

    # Cleanup
    os.remove(micro_path)
    os.remove(macro_path)
    os.rmdir(data_dir)

def test_happy_path(runner, setup_data):
    symbol, micro_path, macro_path = setup_data
    
    result = runner.run_temporal_analysis(symbol=symbol, data_dir=os.path.dirname(__file__))
    assert len(result) > 0

def test_empty_data(runner, setup_data):
    symbol, micro_path, macro_path = setup_data
    os.remove(micro_path)

    with pytest.raises(SystemExit) as exc_info:
        runner.run_temporal_analysis(symbol=symbol, data_dir=os.path.dirname(__file__))
    assert exc_info.type == SystemExit
    assert exc_info.value.code == 1

def test_none_data(runner, setup_data):
    symbol, micro_path, macro_path = setup_data
    os.rename(micro_path, f"{micro_path}_backup")
    
    with pytest.raises(SystemExit) as exc_info:
        runner.run_temporal_analysis(symbol=symbol, data_dir=os.path.dirname(__file__))
    assert exc_info.type == SystemExit
    assert exc_info.value.code == 1

def test_invalid_symbol(runner):
    with pytest.raises(SystemExit) as exc_info:
        runner.run_temporal_analysis(symbol="INVALID", data_dir=os.path.dirname(__file__))
    assert exc_info.type == SystemExit
    assert exc_info.value.code == 1