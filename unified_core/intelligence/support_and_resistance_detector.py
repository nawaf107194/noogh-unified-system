import pandas as pd

class SupportAndResistanceDetector:
    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher
        self.support_levels = []
        self.resistance_levels = []

    def fetch_recent_data(self, symbol, timeframe, lookback_periods):
        """Fetches recent OHLCV data for a given symbol and timeframe."""
        return self.data_fetcher.fetch(symbol, timeframe, lookback_periods)

    def detect_swing_highs_lows(self, data, window_size=5):
        """Detects swing highs and lows using rolling windows."""
        high_series = data['high'].rolling(window=window_size).max()
        low_series = data['low'].rolling(window=window_size).min()
        
        swing_highs = data[high_series == data['high']]
        swing_lows = data[low_series == data['low']]
        
        return swing_highs, swing_lows

    def identify_support_resistance(self, swing_highs, swing_lows):
        """Identifies support and resistance levels from swing highs and lows."""
        self.support_levels = swing_lows['low'].unique().tolist()
        self.resistance_levels = swing_highs['high'].unique().tolist()

    def update_levels(self, symbol, timeframe='1h', lookback_periods=100):
        """Updates support and resistance levels for a given symbol."""
        data = self.fetch_recent_data(symbol, timeframe, lookback_periods)
        swing_highs, swing_lows = self.detect_swing_highs_lows(data)
        self.identify_support_resistance(swing_highs, swing_lows)

    def get_levels(self):
        """Returns the current support and resistance levels."""
        return self.support_levels, self.resistance_levels

# Example usage:
# detector = SupportAndResistanceDetector(MarketDataFetcher())
# detector.update_levels('BTCUSDT')
# supports, resistances = detector.get_levels()