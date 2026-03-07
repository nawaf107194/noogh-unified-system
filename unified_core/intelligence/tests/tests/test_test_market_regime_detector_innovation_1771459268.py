import pytest
import numpy as np

class TestMarketRegimeDetector:
    @pytest.fixture
    def detector(self):
        # Assuming the detector is initialized somewhere in the module
        from unified_core.intelligence.market_regime_detector import MarketRegimeDetector
        return MarketRegimeDetector()

    def test_is_ranging_happy_path(self, detector):
        rsi = np.array([50, 50])
        atr = np.array([1.2, 1.2])
        assert detector.is_ranging(rsi, atr) == True

    def test_is_ranging_empty_input(self, detector):
        rsi = np.array([])
        atr = np.array([])
        with pytest.raises(ValueError, match="Input arrays must not be empty"):
            detector.is_ranging(rsi, atr)

    def test_is_ranging_none_input(self, detector):
        with pytest.raises(TypeError, match="Input must be of type ndarray"):
            detector.is_ranging(None, None)

    def test_is_ranging_boundary_values(self, detector):
        rsi = np.array([30, 70])
        atr = np.array([1, 1.5])
        assert detector.is_ranging(rsi, atr) == False

    def test_is_ranging_invalid_input_types(self, detector):
        rsi = [30, 70]
        atr = [1, 1.5]
        with pytest.raises(TypeError, match="Input must be of type ndarray"):
            detector.is_ranging(rsi, atr)

    def test_is_ranging_invalid_input_shapes(self, detector):
        rsi = np.array([30])
        atr = np.array([1, 1.5])
        with pytest.raises(ValueError, match="Input arrays must have the same length"):
            detector.is_ranging(rsi, atr)

    def test_is_ranging_async_behavior(self, detector):
        # Assuming there's an async version of the method called `is_ranging_async`
        import asyncio

        async def test():
            rsi = np.array([50, 50])
            atr = np.array([1.2, 1.2])
            result = await detector.is_ranging_async(rsi, atr)
            assert result == True

        asyncio.run(test())