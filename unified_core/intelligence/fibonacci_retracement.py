import numpy as np

class FibonacciRetracement:
    """
    Calculates Fibonacci retracement levels for a given price range.
    These levels are used to set intelligent Take Profit and Stop Loss points.
    """
    
    def __init__(self, high_price, low_price):
        self.high_price = high_price
        self.low_price = low_price
        self.fib_levels = self.calculate_fib_levels()
        
    def calculate_fib_levels(self):
        diff = self.high_price - self.low_price
        levels = {
            '0%': self.high_price,
            '23.6%': self.high_price - diff * 0.236,
            '38.2%': self.high_price - diff * 0.382,
            '50%': self.high_price - diff * 0.5,
            '61.8%': self.high_price - diff * 0.618,
            '100%': self.low_price
        }
        return levels
    
    def get_fib_levels(self):
        return self.fib_levels
    
    def suggest_tp_sl(self, current_price, trade_direction):
        """
        Suggests Take Profit and Stop Loss levels based on the current price and trade direction.
        :param current_price: The current price of the asset.
        :param trade_direction: 'LONG' or 'SHORT'.
        :return: A tuple containing suggested TP and SL levels.
        """
        if trade_direction == 'LONG':
            # For long trades, TP should be above the current price and SL below.
            tp_options = [level for level in self.fib_levels.values() if level > current_price]
            sl_options = [level for level in self.fib_levels.values() if level < current_price]
            
            tp = min(tp_options) if tp_options else self.high_price
            sl = max(sl_options) if sl_options else self.low_price
            
        elif trade_direction == 'SHORT':
            # For short trades, TP should be below the current price and SL above.
            tp_options = [level for level in self.fib_levels.values() if level < current_price]
            sl_options = [level for level in self.fib_levels.values() if level > current_price]
            
            tp = max(tp_options) if tp_options else self.low_price
            sl = min(sl_options) if sl_options else self.high_price
            
        else:
            raise ValueError("Invalid trade direction provided.")
        
        return tp, sl