import pytest
from unittest.mock import Mock, AsyncMock

class TestMarketRegimeDetector:

    @pytest.fixture
    def mock_detector(self):
        detector = MarketRegimeDetector()
        detector.data_fetcher = Mock()
        return detector

    @pytest.mark.asyncio
    async def test_fetch_data_happy_path(self, mock_detector):
        # Arrange
        symbol = 'AAPL'
        timeframe = '1d'
        expected_data = [{'timestamp': 1609456800, 'open': 123.45, 'high': 124.56, 'low': 122.34, 'close': 123.56}]
        mock_detector.data_fetcher.fetch_ohlcv.return_value = expected_data
        
        # Act
        result = await mock_detector.fetch_data(symbol, timeframe)
        
        # Assert
        assert result == expected_data
        mock_detector.data_fetcher.fetch_ohlcv.assert_called_once_with(symbol, timeframe)

    @pytest.mark.asyncio
    async def test_fetch_data_edge_cases(self, mock_detector):
        # Empty string
        result = await mock_detector.fetch_data("", "1d")
        mock_detector.data_fetcher.fetch_ohlcv.assert_called_once_with("", "1d")

        # None symbol
        result = await mock_detector.fetch_data(None, "1d")
        mock_detector.data_fetcher.fetch_ohlcv.assert_called_with(None, "1d")

        # Boundary case - minimum timeframe
        result = await mock_detector.fetch_data("AAPL", "1m")
        mock_detector.data_fetcher.fetch_ohlcv.assert_called_with("AAPL", "1m")

    @pytest.mark.asyncio
    async def test_fetch_data_error_cases(self, mock_detector):
        # Invalid symbol type
        with pytest.raises(TypeError):
            await mock_detector.fetch_data(123, "1d")

        # Invalid timeframe type
        with pytest.raises(TypeError):
            await mock_detector.fetch_data("AAPL", 123)

        # Invalid timeframe value
        with pytest.raises(ValueError):
            await mock_detector.fetch_data("AAPL", "1y")

    @pytest.mark.asyncio
    async def test_fetch_data_async_behavior(self, mock_detector):
        # Ensure that fetch_data is an async method
        assert isinstance(mock_detector.fetch_data, AsyncMock)