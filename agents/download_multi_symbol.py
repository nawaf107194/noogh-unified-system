#!/usr/bin/env python3
"""
Multi-Symbol Data Download
===========================
Downloads 12 months of data for BTC, ETH, BNB, SOL
"""

import os
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from binance.client import Client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")
client = Client(API_KEY, API_SECRET)


def download_historical_data(symbol: str, interval: str, start_str: str, end_str: str = None) -> pd.DataFrame:
    """Download historical klines"""
    logger.info(f"📥 {symbol} {interval}...")

    try:
        klines = client.futures_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_str,
            end_str=end_str
        )

        if not klines:
            logger.error(f"❌ No data for {symbol}")
            return pd.DataFrame()

        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume', 'taker_buy_base', 'taker_buy_quote']:
            df[col] = df[col].astype(float)

        df.set_index('timestamp', inplace=True)

        logger.info(f"   ✅ {len(df)} candles | {df.index[0]} → {df.index[-1]}")
        return df

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return pd.DataFrame()


def main():
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]

    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=365)

    start_str = start_dt.strftime("%d %b %Y %H:%M:%S")
    end_str = end_dt.strftime("%d %b %Y %H:%M:%S")

    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    logger.info("="*70)
    logger.info("🏛️ MULTI-SYMBOL DATA DOWNLOAD")
    logger.info("="*70)
    logger.info(f"Symbols: {', '.join(symbols)}")
    logger.info(f"Period: {start_str} → {end_str}")
    logger.info("="*70)

    for symbol in symbols:
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 {symbol}")
        logger.info(f"{'='*70}")

        # 5m
        df_5m = download_historical_data(symbol, '5m', start_str, end_str)
        if not df_5m.empty:
            output = data_dir / f"{symbol}_5m_12M.parquet"
            df_5m.to_parquet(output)
            logger.info(f"   💾 {output.name} ({len(df_5m):,} rows)")

        # 1h
        df_1h = download_historical_data(symbol, '1h', start_str, end_str)
        if not df_1h.empty:
            output = data_dir / f"{symbol}_1h_12M.parquet"
            df_1h.to_parquet(output)
            logger.info(f"   💾 {output.name} ({len(df_1h):,} rows)")

    logger.info(f"\n{'='*70}")
    logger.info("✅ MULTI-SYMBOL DOWNLOAD COMPLETE")
    logger.info("="*70)


if __name__ == "__main__":
    main()
