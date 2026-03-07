# unified_core/intelligence/funding_rate_filter.py

import asyncio
from datetime import datetime
from typing import Optional

class FundingRateFilter:
    def __init__(self):
        self.last_funding_rate = None
        self.high_threshold = 0.1 / 100  # 0.1% funding rate threshold
        self.low_threshold = -0.1 / 100  # -0.1% funding rate threshold

    async def should_trade(self, current_funding_rate: float) -> bool:
        """
        Determines if a trade should be executed based on the current funding rate.
        
        :param current_funding_rate: The current funding rate from Binance API
        :return: True if it's safe to trade, False otherwise
        """
        self.last_funding_rate = current_funding_rate

        # Avoid long positions when funding rate is high (indicating a potential sell-off)
        if current_funding_rate > self.high_threshold:
            return False
        
        return True

    def get_last_funding_rate(self) -> Optional[float]:
        """
        Returns the last recorded funding rate.
        
        :return: The last funding rate or None if not set
        """
        return self.last_funding_rate


async def main():
    filter = FundingRateFilter()
    
    # Simulated funding rates for testing
    simulated_rates = [0.12, 0.05, -0.08, -0.03, 0.15]
    
    for rate in simulated_rates:
        print(f"Current funding rate: {rate}% - Trade allowed: {await filter.should_trade(rate)}")


if __name__ == "__main__":
    asyncio.run(main())