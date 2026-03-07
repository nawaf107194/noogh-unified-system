# unified_core/intelligence/multi_timeframe_confluence_checker.py

import pandas as pd
from unified_core.intelligence.world_model import WorldModel

class MultiTimeframeConfluenceChecker:
    def __init__(self):
        self.world_model = WorldModel()

    def check_confluence(self, symbol, timeframes):
        confluence_data = {}
        for timeframe in timeframes:
            historical_data = self.world_model.get_historical_data(symbol, timeframe)
            indicators = self.calculate_indicators(historical_data)
            confluence_data[timeframe] = indicators
        
        return self.evaluate_confluence(confluence_data)

    def calculate_indicators(self, data):
        # Example: Calculate RSI and MACD for simplicity
        data['RSI'] = self.world_model.get_rsi(data['close'])
        data['MACD'], _ = self.world_model.get_macd(data['close'])
        return {'RSI': data['RSI'].iloc[-1], 'MACD': data['MACD'].iloc[-1]}

    def evaluate_confluence(self, confluence_data):
        # Check if all indicators are within acceptable ranges
        for timeframe, indicators in confluence_data.items():
            if not (0 < indicators['RSI'] < 70 and -50 > indicators['MACD'] > -200):
                return False
        return True

if __name__ == '__main__':
    checker = MultiTimeframeConfluenceChecker()
    timeframes = ['1d', '4h', '1h']
    symbol = 'BTC/USD'
    
    if checker.check_confluence(symbol, timeframes):
        print("All indicators are in confluence. Proceed with decision.")
    else:
        print("Indicators diverge. Aborting decision.")