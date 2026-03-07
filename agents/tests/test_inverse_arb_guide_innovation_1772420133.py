import pytest
from agents.inverse_arb_guide import InverseArbGuide

API_KEY = "your_api_key"
API_SECRET = "your_api_secret"

def test_normal_inputs():
    guide = InverseArbGuide(symbol="BTCUSDT", capital_usdt=1000)
    assert guide.symbol == "BTCUSDT"
    assert guide.capital == 1000

def test_empty_symbol():
    with pytest.raises(ValueError):
        InverseArbGuide(symbol="", capital_usdt=1000)

def test_none_symbol():
    with pytest.raises(ValueError):
        InverseArbGuide(symbol=None, capital_usdt=1000)

def test_boundary_capital():
    guide = InverseArbGuide(symbol="BTCUSDT", capital_usdt=0.01)
    assert guide.symbol == "BTCUSDT"
    assert guide.capital == 0.01

def test_negative_capital():
    with pytest.raises(ValueError):
        InverseArbGuide(symbol="BTCUSDT", capital_usdt=-100)

def test_large_capital():
    guide = InverseArbGuide(symbol="BTCUSDT", capital_usdt=1e12)
    assert guide.symbol == "BTCUSDT"
    assert guide.capital == 1e12

def test_non_numeric_capital():
    with pytest.raises(ValueError):
        InverseArbGuide(symbol="BTCUSDT", capital_usdt="1000")

def test_empty_symbol_async():
    with pytest.raises(ValueError):
        async def create_guide():
            return await InverseArbGuide(symbol="", capital_usdt=1000)
        
        asyncio.run(create_guide())

def test_none_symbol_async():
    with pytest.raises(ValueError):
        async def create_guide():
            return await InverseArbGuide(symbol=None, capital_usdt=1000)
        
        asyncio.run(create_guide())

def test_boundary_capital_async():
    with pytest.raises(ValueError):
        async def create_guide():
            return await InverseArbGuide(symbol="BTCUSDT", capital_usdt=0.01)
        
        asyncio.run(create_guide())