import pytest
from unified_core.intelligence.btc_correlation_guard import BTCCorrelationGuard

@pytest.fixture
def guard():
    return BTCCorrelationGuard()

def test_happy_path(guard):
    signals = [
        {'type': 'buy', 'price': 100},
        {'type': 'sell', 'price': 200}
    ]
    result = guard.process_trading_signals(signals)
    assert len(result) == 2
    assert all(isinstance(signal, dict) for signal in result)

def test_edge_case_empty(guard):
    signals = []
    result = guard.process_trading_signals(signals)
    assert len(result) == 0

def test_edge_case_none(guard):
    signals = None
    result = guard.process_trading_signals(signals)
    assert result is None

def test_error_case_invalid_input(guard):
    signals = 'not a list'
    with pytest.raises(TypeError):
        guard.process_trading_signals(signals)

@pytest.mark.asyncio
async def test_async_behavior(guard):
    async def apply_guard(signal):
        return signal['type'] == 'buy'

    guard.apply_guard = apply_guard

    signals = [
        {'type': 'buy', 'price': 100},
        {'type': 'sell', 'price': 200}
    ]
    result = await guard.process_trading_signals(signals)
    assert len(result) == 1
    assert all(isinstance(signal, dict) for signal in result)