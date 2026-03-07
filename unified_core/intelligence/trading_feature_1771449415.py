import numpy as np

class SupportResistanceDetector:
    def __init__(self, price_data, lookback=20):
        """
        Initialize the detector with price data and lookback period.
        
        :param price_data: List or array of historical prices.
        :param lookback: Number of periods to look back for detecting swings.
        """
        self.price_data = price_data
        self.lookback = lookback
        self.support_levels = []
        self.resistance_levels = []

    def detect_swings(self):
        """
        Detects swing highs and lows within the lookback period.
        """
        for i in range(self.lookback, len(self.price_data)):
            high = max(self.price_data[i-self.lookback:i])
            low = min(self.price_data[i-self.lookback:i])
            if self.price_data[i] == high:
                self.resistance_levels.append(high)
            elif self.price_data[i] == low:
                self.support_levels.append(low)

    def get_levels(self):
        """
        Returns the detected support and resistance levels.
        """
        return {
            'support': self.support_levels,
            'resistance': self.resistance_levels
        }

# Example usage
if __name__ == "__main__":
    # Example price data
    price_data = [100, 102, 101, 103, 105, 104, 106, 107, 105, 104, 103, 102, 101, 100]
    detector = SupportResistanceDetector(price_data, lookback=5)
    detector.detect_swings()
    levels = detector.get_levels()
    print("Support Levels:", levels['support'])
    print("Resistance Levels:", levels['resistance'])