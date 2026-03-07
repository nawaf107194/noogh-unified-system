#!/usr/bin/env python3
"""
Download 12 Months Historical Data
===================================
Production-grade data downloader for institutional backtesting
"""

import os
import sys
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

# Unauthenticated client (public data only)
API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")
client = Client(API_KEY, API_SECRET)


def download_historical_data(
    symbol: str,
    interval: str,
    start_str: str,
    end_str: str = None
) -> pd.DataFrame:
    """
    Download historical klines with automatic pagination

    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        interval: Timeframe (5m, 1h, etc.)
        start_str: Start date (e.g., "1 Mar 2025")
        end_str: End date (optional)

    Returns:
        DataFrame with OHLCV data
    """
    logger.info(f"📥 Downloading {symbol} {interval} from {start_str} to {end_str or 'now'}...")

    try:
        # Fetch klines (automatically handles pagination)
        klines = client.futures_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_str,
            end_str=end_str
        )

        if not klines:
            logger.error(f"❌ No data fetched for {symbol} {interval}")
            return pd.DataFrame()

        # Convert to DataFrame
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

        logger.info(f"✅ Fetched {len(df)} candles")
        logger.info(f"   Date range: {df.index[0]} → {df.index[-1]}")
        logger.info(f"   Price range: {df['close'].min():.2f} - {df['close'].max():.2f}")

        return df

    except Exception as e:
        logger.error(f"❌ Error downloading data: {e}")
        return pd.DataFrame()


def main():
    """Download 12 months of BTCUSDT data"""

    logger.info("="*70)
    logger.info("🏛️ INSTITUTIONAL DATA DOWNLOAD - 12 MONTHS")
    logger.info("="*70)

    symbol = "BTCUSDT"

    # Calculate date range (12 months)
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=365)

    start_str = start_dt.strftime("%d %b %Y %H:%M:%S")
    end_str = end_dt.strftime("%d %b %Y %H:%M:%S")

    logger.info(f"\n📅 Date Range:")
    logger.info(f"   Start: {start_str}")
    logger.info(f"   End: {end_str}")
    logger.info(f"   Duration: 365 days (~12 months)\n")

    # Data directory
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    # Download 5m data
    logger.info("\n" + "="*70)
    logger.info("📊 MICRO DATA (5m)")
    logger.info("="*70)

    df_5m = download_historical_data(symbol, '5m', start_str, end_str)

    if not df_5m.empty:
        output_5m = data_dir / f"{symbol}_5m_12M.parquet"
        df_5m.to_parquet(output_5m)

        size_mb = output_5m.stat().st_size / (1024 * 1024)
        logger.info(f"💾 Saved: {output_5m}")
        logger.info(f"   Size: {size_mb:.2f} MB")
        logger.info(f"   Rows: {len(df_5m):,}")

    # Download 1h data
    logger.info("\n" + "="*70)
    logger.info("📊 MACRO DATA (1h)")
    logger.info("="*70)

    df_1h = download_historical_data(symbol, '1h', start_str, end_str)

    if not df_1h.empty:
        output_1h = data_dir / f"{symbol}_1h_12M.parquet"
        df_1h.to_parquet(output_1h)

        size_mb = output_1h.stat().st_size / (1024 * 1024)
        logger.info(f"💾 Saved: {output_1h}")
        logger.info(f"   Size: {size_mb:.2f} MB")
        logger.info(f"   Rows: {len(df_1h):,}")

    # Summary
    logger.info("\n" + "="*70)
    logger.info("✅ DOWNLOAD COMPLETE")
    logger.info("="*70)

    if not df_5m.empty and not df_1h.empty:
        logger.info(f"\n📊 Data Quality Check:")
        logger.info(f"   5m candles: {len(df_5m):,}")
        logger.info(f"   1h candles: {len(df_1h):,}")
        logger.info(f"   Expected 5m: ~105,120 (365 days * 288 candles/day)")
        logger.info(f"   Expected 1h: ~8,760 (365 days * 24 hours)")

        coverage_5m = (len(df_5m) / 105120) * 100
        coverage_1h = (len(df_1h) / 8760) * 100

        logger.info(f"\n   Coverage: 5m={coverage_5m:.1f}%, 1h={coverage_1h:.1f}%")

        if coverage_5m > 95 and coverage_1h > 95:
            logger.info(f"\n   ✅ Data quality: EXCELLENT")
        elif coverage_5m > 90 and coverage_1h > 90:
            logger.info(f"\n   ⚠️  Data quality: GOOD (minor gaps)")
        else:
            logger.info(f"\n   ⚠️  Data quality: CHECK FOR GAPS")

    logger.info("\n🚀 Ready for setup generation!")
    logger.info("="*70 + "\n")


if __name__ == "__main__":
    main()
