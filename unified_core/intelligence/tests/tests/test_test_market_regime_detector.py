import pytest

class TestMarketRegimeDetector:
    def test_is_ranging_happy_path(self, detector):
        rsi = 50
        atr = 1.5
        result = detector.is_ranging(rsi, atr)
        assert isinstance(result, bool)

    def test_is_ranging_empty_inputs(self, detector):
        rsi = ""
        atr = ""
        with pytest.raises(TypeError):
            detector.is_ranging(rsi, atr)

    def test_is_ranging_none_inputs(self, detector):
        rsi = None
        atr = None
        with pytest.raises(TypeError):
            detector.is_ranging(rsi, atr)

    def test_is_ranging_boundary_values(self, detector):
        rsi = 0
        atr = 0
        result = detector.is_ranging(rsi, atr)
        assert isinstance(result, bool)

        rsi = 100
        atr = 100
        result = detector.is_ranging(rsi, atr)
        assert isinstance(result, bool)

    def test_is_ranging_invalid_inputs(self, detector):
        rsi = "not a number"
        atr = "not a number"
        with pytest.raises(TypeError):
            detector.is_ranging(rsi, atr)

        rsi = -1
        atr = -1
        with pytest.raises(ValueError):
            detector.is_ranging(rsi, atr)

        rsi = 101
        atr = 101
        with pytest.raises(ValueError):
            detector.is_ranging(rsi, atr)

    @pytest.mark.asyncio
    async def test_is_ranging_async_behavior(self, async_detector):
        rsi = 50
        atr = 1.5
        result = await async_detector.is_ranging(rsi, atr)
        assert isinstance(result, bool)