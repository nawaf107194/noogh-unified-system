import pytest

class TestMarketRegimeDetector:
    @pytest.fixture
    def mock_data_fetcher(self):
        class MockDataFetcher:
            async def fetch_data(self):
                return {"market_data": "mocked"}
        return MockDataFetcher()

    def test_init_with_none_data_fetcher(self):
        with pytest.raises(TypeError):
            MarketRegimeDetector(None)

    def test_init_with_valid_data_fetcher(self, mock_data_fetcher):
        detector = MarketRegimeDetector(mock_data_fetcher)
        assert detector.data_fetcher == mock_data_fetcher

    def test_init_with_empty_data_fetcher(self):
        with pytest.raises(TypeError):
            MarketRegimeDetector("")

    def test_init_with_invalid_data_fetcher_type(self):
        with pytest.raises(TypeError):
            MarketRegimeDetector(123)

    @pytest.mark.asyncio
    async def test_async_behavior(self, mock_data_fetcher):
        detector = MarketRegimeDetector(mock_data_fetcher)
        data = await detector.fetch_market_data()
        assert data == {"market_data": "mocked"}

    def test_init_with_non_callable_data_fetcher(self):
        with pytest.raises(TypeError):
            MarketRegimeDetector({"fetch_data": "not callable"})