import pandas as pd

class PerSymbolWinRateCalibration:
    """
    Adjusts the confidence threshold dynamically based on each symbol's win rate.
    
    Attributes:
        win_rates (dict): A dictionary mapping each symbol to its win rate.
        confidence_thresholds (dict): A dictionary mapping each symbol to its adjusted confidence threshold.
    """
    
    def __init__(self, initial_confidence_threshold=65):
        self.win_rates = {}
        self.confidence_thresholds = {}
        self.initial_confidence_threshold = initial_confidence_threshold
        
    def update_win_rates(self, trade_results):
        """
        Updates the win rates for each symbol based on the latest trade results.
        
        Parameters:
            trade_results (list of dict): A list where each dictionary contains 'symbol', 'win' (bool) and 'timestamp'.
        """
        df = pd.DataFrame(trade_results)
        grouped = df.groupby('symbol')
        self.win_rates = grouped['win'].mean().to_dict()
        
    def adjust_confidence_thresholds(self):
        """
        Adjusts the confidence threshold for each symbol based on its win rate.
        """
        for symbol, win_rate in self.win_rates.items():
            if win_rate < 0.5:
                # If win rate is below 50%, decrease confidence threshold to be more conservative.
                self.confidence_thresholds[symbol] = max(50, self.initial_confidence_threshold - (1 - win_rate) * 10)
            else:
                # If win rate is above 50%, increase confidence threshold to take more aggressive trades.
                self.confidence_thresholds[symbol] = min(80, self.initial_confidence_threshold + win_rate * 10)
                
    def get_confidence_threshold(self, symbol):
        """
        Returns the adjusted confidence threshold for a given symbol.
        
        Parameters:
            symbol (str): The trading symbol.
            
        Returns:
            int: The adjusted confidence threshold for the symbol.
        """
        return self.confidence_thresholds.get(symbol, self.initial_confidence_threshold)
        
# Example usage
if __name__ == "__main__":
    calibrator = PerSymbolWinRateCalibration(initial_confidence_threshold=65)
    trade_results = [
        {'symbol': 'BTCUSDT', 'win': True, 'timestamp': '2023-01-01T12:00:00Z'},
        {'symbol': 'ETHUSDT', 'win': False, 'timestamp': '2023-01-01T12:00:00Z'},
        {'symbol': 'SOLUSDT', 'win': True, 'timestamp': '2023-01-01T12:00:00Z'},
        # ... more trade results
    ]
    calibrator.update_win_rates(trade_results)
    calibrator.adjust_confidence_thresholds()
    print(calibrator.get_confidence_threshold('BTCUSDT'))
    print(calibrator.get_confidence_threshold('ETHUSDT'))
    print(calibrator.get_confidence_threshold('SOLUSDT'))