import pytest

from unified_core.intelligence.funding_rate_filter import FundingRateFilter

class TestFundingRateFilter:

    @pytest.fixture
    def funding_rate_filter(self):
        return FundingRateFilter()

    def test_get_last_funding_rate_happy_path(self, funding_rate_filter):
        # Arrange
        expected_funding_rate = 0.01
        funding_rate_filter.last_funding_rate = expected_funding_rate

        # Act
        result = funding_rate_filter.get_last_funding_rate()

        # Assert
        assert result == expected_funding_rate

    def test_get_last_funding_rate_none(self, funding_rate_filter):
        # Arrange
        funding_rate_filter.last_funding_rate = None

        # Act
        result = funding_rate_filter.get_last_funding_rate()

        # Assert
        assert result is None