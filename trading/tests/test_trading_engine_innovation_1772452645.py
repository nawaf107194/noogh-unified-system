import pytest
from trading.trading_engine import get_trading_engine, TradingEngine

@pytest.fixture(autouse=True)
def reset_global_state():
    global _trading_engine
    _trading_engine = None

def test_get_trading_engine_happy_path():
    engine1 = get_trading_engine()
    engine2 = get_trading_engine()
    assert engine1 is engine2, "Engine should be a singleton"

def test_get_trading_engine_testnet_true():
    engine = get_trading_engine(testnet=True)
    assert engine.testnet is True, "Testnet flag should be True"

def test_get_trading_engine_read_only_false():
    engine = get_trading_engine(read_only=False)
    assert engine.read_only is False, "Read-only flag should be False"

def test_get_trading_engine_testnet_false():
    engine = get_trading_engine(testnet=False)
    assert engine.testnet is False, "Testnet flag should be False"

def test_get_trading_engine_read_only_true():
    engine = get_trading_engine(read_only=True)
    assert engine.read_only is True, "Read-only flag should be True"