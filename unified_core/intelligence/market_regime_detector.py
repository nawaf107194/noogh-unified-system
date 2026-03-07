import numpy as np
from talib import abstract

class MarketRegimeDetector:
    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher
        self.regimes = {
            'Trending': self.is_trending,
            'Ranging': self.is_ranging,
            'Volatile': self.is_volatile
        }

    def fetch_data(self, symbol, timeframe):
        return self.data_fetcher.fetch_ohlcv(symbol, timeframe)

    def calculate_indicators(self, data):
        close = data['close']
        rsi = abstract.RSI(close, timeperiod=14)
        atr = abstract.ATR(data['high'], data['low'], close, timeperiod=14)
        return rsi, atr

    def is_trending(self, rsi, atr):
        return np.mean(rsi) > 70 or np.mean(rsi) < 30

    def is_ranging(self, rsi, atr):
        return 30 <= np.mean(rsi) <= 70 and np.std(atr) < 1.5 * np.mean(atr)

    def is_volatile(self, rsi, atr):
        return np.std(atr) > 1.5 * np.mean(atr)

    def detect_regime(self, symbol, timeframe='1h'):
        data = self.fetch_data(symbol, timeframe)
        rsi, atr = self.calculate_indicators(data)
        for regime, condition in self.regimes.items():
            if condition(rsi, atr):
                return regime
        return 'Unknown'

# Example usage within the trading engine
if __name__ == "__main__":
    # Assuming MarketDataFetcher is already defined and initialized
    detector = MarketRegimeDetector(MarketDataFetcher())
    regime = detector.detect_regime('BTCUSDT')
    print(f"Detected regime for BTCUSDT: {regime}")