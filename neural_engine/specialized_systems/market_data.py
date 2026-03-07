import logging
import random

logger = logging.getLogger(__name__)


class MarketData:
    """
    Fetches financial market data (Mocked for Phase 4).
    """

    def __init__(self):
        logger.info("MarketData initialized.")

    def get_price(self, symbol: str) -> float:
        """
        Get current price for a symbol.
        """
        # Mock logic
        base_prices = {"AAPL": 150.0, "GOOGL": 2800.0, "BTC": 45000.0}
        price = base_prices.get(symbol.upper(), 100.0)

        # Add random fluctuation
        variation = random.uniform(-0.02, 0.02)
        final_price = price * (1 + variation)

        logger.info(f"Fetched price for {symbol}: {final_price:.2f}")
        return round(final_price, 2)
