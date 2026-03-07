import pytest

class TradingFeatureTest:

    @pytest.fixture
    def trading_feature(self):
        return TradingFeature(price_data=[10, 12, 15, 14, 16], lookback=3)

    def test_happy_path(self, trading_feature):
        assert len(trading_feature.price_data) == 5
        assert trading_feature.lookback == 3
        assert trading_feature.support_levels == []
        assert trading_feature.resistance_levels == []

    def test_empty_price_data(self):
        tf = TradingFeature(price_data=[], lookback=20)
        assert len(tf.price_data) == 0
        assert tf.lookback == 20
        assert tf.support_levels == []
        assert tf.resistance_levels == []

    def test_none_price_data(self):
        tf = TradingFeature(price_data=None, lookback=10)
        assert tf.price_data is None
        assert tf.lookback == 10
        assert tf.support_levels == []
        assert tf.resistance_levels == []

    def test_negative_lookback(self):
        with pytest.raises(ValueError) as exc_info:
            trading_feature = TradingFeature(price_data=[10, 20], lookback=-5)
        assert "lookback must be a positive integer" in str(exc_info.value)

    def test_zero_lookback(self):
        with pytest.raises(ValueError) as exc_info:
            trading_feature = TradingFeature(price_data=[10, 20, 30], lookback=0)
        assert "lookback must be a positive integer" in str(exc_info.value)

    def test_non_integer_lookback(self):
        with pytest.raises(ValueError) as exc_info:
            trading_feature = TradingFeature(price_data=[10, 20, 30], lookback=3.5)
        assert "lookback must be an integer" in str(exc_info.value)