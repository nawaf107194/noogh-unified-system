import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_data_fetcher():
    return Mock()

@pytest.fixture
def market_regime_detector(mock_data_fetcher):
    from unified_core.intelligence.market_regime_detector import MarketRegimeDetector
    regimes = {
        'Trending': lambda x: x,
        'Ranging': lambda x: x,
        'Volatile': lambda x: x
    }
    return MarketRegimeDetector(mock_data_fetcher, regimes)

def test_init_happy_path(market_regime_detector):
    assert market_regime_detector.data_fetcher == mock_data_fetcher
    assert len(market_regime_detector.regimes) == 3
    assert callable(market_regime_detector.regimes['Trending'])
    assert callable(market_regime_detector.regimes['Ranging'])
    assert callable(market_regime_detector.regimes['Volatile'])

def test_init_with_empty_regimes(mock_data_fetcher):
    from unified_core.intelligence.market_regime_detector import MarketRegimeDetector
    with pytest.raises(ValueError, match="At least one regime must be defined"):
        MarketRegimeDetector(mock_data_fetcher, {})

def test_init_with_none_regimes(mock_data_fetcher):
    from unified_core.intelligence.market_regime_detector import MarketRegimeDetector
    with pytest.raises(TypeError, match="regimes must be a dictionary"):
        MarketRegimeDetector(mock_data_fetcher, None)

def test_init_with_invalid_regime_names(mock_data_fetcher):
    from unified_core.intelligence.market_regime_detector import MarketRegimeDetector
    invalid_regimes = {
        123: lambda x: x,
        True: lambda x: x,
        "Invalid Name": lambda x: x
    }
    with pytest.raises(ValueError, match="Regime names must be strings"):
        MarketRegimeDetector(mock_data_fetcher, invalid_regimes)

def test_init_with_non_callable_regime_functions(mock_data_fetcher):
    from unified_core.intelligence.market_regime_detector import MarketRegimeDetector
    non_callable_regimes = {
        'Trending': 123,
        'Ranging': "Not a function",
        'Volatile': [1, 2, 3]
    }
    with pytest.raises(TypeError, match="All regime functions must be callable"):
        MarketRegimeDetector(mock_data_fetcher, non_callable_regimes)

@pytest.mark.asyncio
async def test_async_init_behavior(market_regime_detector):
    # Assuming there is an async method in MarketRegimeDetector, for example, fetch_data()
    data = await market_regime_detector.fetch_data()
    assert data == mock_data_fetcher.return_value