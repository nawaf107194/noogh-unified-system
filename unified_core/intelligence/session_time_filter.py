import pytz
from datetime import datetime

class SessionTimeFilter:
    def __init__(self, timezone='UTC'):
        self.timezone = pytz.timezone(timezone)

    def is_liquid_time(self):
        """
        Check if the current time is outside of the low liquidity period (02:00-06:00 UTC).
        
        Returns:
            bool: True if it's a liquid time, False otherwise.
        """
        now = datetime.now(self.timezone)
        hour = now.hour
        
        # Define low liquidity period
        low_liquidity_start = 2  # 02:00
        low_liquidity_end = 6    # 06:00
        
        # Check if current hour is within low liquidity period
        if low_liquidity_start <= hour < low_liquidity_end:
            return False
        else:
            return True

# Example usage
if __name__ == "__main__":
    time_filter = SessionTimeFilter()
    if time_filter.is_liquid_time():
        print("Current time is liquid.")
    else:
        print("Avoid trading, current time is low liquidity.")