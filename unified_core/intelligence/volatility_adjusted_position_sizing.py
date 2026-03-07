import numpy as np

class VolatilityAdjustedPositionSizing:
    def __init__(self, base_leverage=20, max_leverage=50, min_leverage=5):
        self.base_leverage = base_leverage
        self.max_leverage = max_leverage
        self.min_leverage = min_leverage

    def calculate_volatility(self, price_data):
        """
        Calculate the rolling standard deviation (volatility) of the given price data.
        :param price_data: List of historical closing prices.
        :return: Volatility (rolling standard deviation).
        """
        # Calculate rolling standard deviation over the last 20 periods
        return np.std(price_data[-20:], ddof=1)

    def adjust_position_size(self, volatility, current_price, max_expected_volatility=50.0):
        """
        Adjust the position size based on the calculated volatility.
        :param volatility: The calculated volatility.
        :param current_price: Current market price.
        :param max_expected_volatility: Assumed maximum volatility for normalization.
        :return: Adjusted leverage and position size.
        """
        # Normalize volatility to a range between min and max leverage
        # Higher volatility should lead to lower leverage (safer)
        normalized_volatility = np.interp(volatility, [0, max_expected_volatility], [self.max_leverage, self.min_leverage])
        adjusted_leverage = np.clip(normalized_volatility, self.min_leverage, self.max_leverage)
        
        # Calculate position size based on adjusted leverage
        position_size = current_price * adjusted_leverage
        
        return adjusted_leverage, position_size

# Example usage:
if __name__ == "__main__":
    # Mock historical price data
    price_data = [np.random.uniform(1000, 1100) for _ in range(100)]
    current_price = price_data[-1]

    # Initialize the volatility adjusted position sizing model
    model = VolatilityAdjustedPositionSizing()

    # Calculate the volatility
    volatility = model.calculate_volatility(price_data)

    # Adjust the position size based on the calculated volatility
    adjusted_leverage, position_size = model.adjust_position_size(volatility, current_price)

    print(f"Current Price: {current_price}")
    print(f"Calculated Volatility: {volatility}")
    print(f"Adjusted Leverage: {adjusted_leverage}")
    print(f"Position Size: {position_size}")