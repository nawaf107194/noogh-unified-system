import pytest
from unittest.mock import MagicMock, AsyncMock

class MockDataFetcher:
    def __init__(self):
        self.fetch = AsyncMock()

@pytest.fixture
def mock_support_and_resistance_detector():
    mock_detector = MagicMock()
    mock_detector.data_fetcher = MockDataFetcher()
    return mock_detector

@pytest.mark.asyncio
async def test_fetch_recent_data_happy_path(mock_support_and_resistance_detector):
    # Arrange
    symbol = 'AAPL'
    timeframe = '1h'
    lookback_periods = 50
    expected_data = [{'timestamp': 1625000000, 'open': 150.0, 'high': 152.0, 'low': 149.0, 'close': 151.0, 'volume': 10000}]
    mock_support_and_resistance_detector.data_fetcher.fetch.return_value = expected_data

    # Act
    result = await mock_support_and_resistance_detector.fetch_recent_data(symbol, timeframe, lookback_periods)

    # Assert
    assert result == expected_data
    mock_support_and_resistance_detector.data_fetcher.fetch.assert_called_once_with(symbol, timeframe, lookback_periods)

@pytest.mark.asyncio
async def test_fetch_recent_data_edge_case_empty_lookback_periods(mock_support_and_resistance_detector):
    # Arrange
    symbol = 'AAPL'
    timeframe = '1h'
    lookback_periods = 0
    expected_data = []
    mock_support_and_resistance_detector.data_fetcher.fetch.return_value = expected_data

    # Act
    result = await mock_support_and_resistance_detector.fetch_recent_data(symbol, timeframe, lookback_periods)

    # Assert
    assert result == expected_data
    mock_support_and_resistance_detector.data_fetcher.fetch.assert_called_once_with(symbol, timeframe, lookback_periods)

@pytest.mark.asyncio
async def test_fetch_recent_data_edge_case_none_symbol(mock_support_and_resistance_detector):
    # Arrange
    symbol = None
    timeframe = '1h'
    lookback_periods = 50

    # Act & Assert
    with pytest.raises(ValueError, match="symbol cannot be None"):
        await mock_support_and_resistance_detector.fetch_recent_data(symbol, timeframe, lookback_periods)

@pytest.mark.asyncio
async def test_fetch_recent_data_error_case_invalid_timeframe(mock_support_and_resistance_detector):
    # Arrange
    symbol = 'AAPL'
    timeframe = 'invalid'
    lookback_periods = 50

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid timeframe provided"):
        await mock_support_and_resistance_detector.fetch_recent_data(symbol, timeframe, lookback_periods)

@pytest.mark.asyncio
async def test_fetch_recent_data_async_behavior(mock_support_and_resistance_detector):
    # Arrange
    symbol = 'AAPL'
    timeframe = '1h'
    lookback_periods = 50
    expected_data = [{'timestamp': 1625000000, 'open': 150.0, 'high': 152.0, 'low': 149.0, 'close': 151.0, 'volume': 10000}]
    mock_support_and_resistance_detector.data_fetcher.fetch.return_value = expected_data

    # Act
    result = await mock_support_and_resistance_detector.fetch_recent_data(symbol, timeframe, lookback_periods)

    # Assert
    assert result == expected_data
    mock_support_and_resistance_detector.data_fetcher.fetch.assert_awaited_once_with(symbol, timeframe, lookback_periods)