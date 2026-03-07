import os
import time
import logging
import pandas as pd
from datetime import datetime, timedelta
from binance.client import Client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to get API keys from env if available, otherwise initialized unauthenticated
API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")

client = Client(API_KEY, API_SECRET)

def download_historical_data(symbol: str, interval: str, start_str: str, end_str: str = None) -> pd.DataFrame:
    """Download historical klines using python-binance's paginated fetcher."""
    logger.info(f"Downloading {symbol} {interval} from {start_str} to {end_str or 'now'}...")
    
    # Fetch klines
    klines = client.futures_historical_klines(
        symbol=symbol,
        interval=interval,
        start_str=start_str,
        end_str=end_str
    )
    
    if not klines:
        logger.error(f"No data fetched for {symbol} {interval}")
        return pd.DataFrame()
        
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    
    # Convert types
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume', 'taker_buy_base', 'taker_buy_quote']:
        df[col] = df[col].astype(float)
        
    df.set_index('timestamp', inplace=True)
    logger.info(f"Fetched {len(df)} bars.")
    return df

def main():
    symbol = "BTCUSDT"
    
    # Let's fetch the last 3 months
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=90)
    
    start_str = start_dt.strftime("%d %b %Y %H:%M:%S")
    end_str = end_dt.strftime("%d %b %Y %H:%M:%S")
    
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Micro Data (5m)
    df_micro = download_historical_data(symbol, '5m', start_str, end_str)
    if not df_micro.empty:
        micro_path = os.path.join(data_dir, f"{symbol}_5m_3M.parquet")
        df_micro.to_parquet(micro_path)
        logger.info(f"Saved micro data to {micro_path}")
        
    # Macro Data (1h)
    df_macro = download_historical_data(symbol, '1h', start_str, end_str)
    if not df_macro.empty:
        macro_path = os.path.join(data_dir, f"{symbol}_1h_3M.parquet")
        df_macro.to_parquet(macro_path)
        logger.info(f"Saved macro data to {macro_path}")

if __name__ == "__main__":
    main()
