import pytest

class MockDataFetcher:
    def fetch_data(self):
        return {
            'Trending': True,
            'Ranging': False,
            'Volatile': True
        }

class TestMarketRegimeDetector:

    @pytest.fixture
    def detector(self):
        data_fetcher = MockDataFetcher()
        return MarketRegimeDetector(data_fetcher)

    def test_happy_path(self, detector):
        assert detector.data_fetcher == MockDataFetcher()
        assert len(detector.regimes) == 3
        assert callable(detector.regimes['Trending'])
        assert callable(detector.regimes['Ranging'])
        assert callable(detector.regimes['Volatile'])

    def test_edge_case_none_data_fetcher(self):
        with pytest.raises(TypeError):
            MarketRegimeDetector(None)

    def test_edge_case_empty_data_fetcher(self):
        class EmptyDataFetcher:
            pass
        with pytest.raises(TypeError):
            MarketRegimeDetector(EmptyDataFetcher())

    def test_error_case_invalid_data_fetcher(self):
        class InvalidDataFetcher:
            fetch_data = 123  # Not a callable
        with pytest.raises(TypeError):
            MarketRegimeDetector(InvalidDataFetcher())