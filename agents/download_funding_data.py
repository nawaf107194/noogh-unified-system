#!/usr/bin/env python3
"""
Download Funding Rate Data
===========================
Downloads historical funding rates + price data for funding strategy
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


def download_funding_rate_history(symbol: str, start_time: datetime, end_time: datetime = None) -> pd.DataFrame:
    """
    Download funding rate history from Binance Futures

    Funding rate is collected every 8 hours (00:00, 08:00, 16:00 UTC)
    """
    logger.info(f"📥 Downloading funding rates for {symbol}...")

    try:
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000) if end_time else int(datetime.utcnow().timestamp() * 1000)

        funding_rates = []
        current_start = start_ms

        # Binance API returns max 1000 records per call
        # Funding happens every 8h, so 1000 records = ~333 days
        while current_start < end_ms:
            try:
                rates = client.futures_funding_rate(
                    symbol=symbol,
                    startTime=current_start,
                    endTime=end_ms,
                    limit=1000
                )

                if not rates:
                    break

                funding_rates.extend(rates)

                # Update start time for next batch
                current_start = rates[-1]['fundingTime'] + 1

                logger.info(f"   Fetched {len(rates)} funding records (total: {len(funding_rates)})")

                if len(rates) < 1000:
                    break  # No more data

            except Exception as e:
                logger.error(f"   Error fetching batch: {e}")
                break

        if not funding_rates:
            logger.error(f"❌ No funding rate data for {symbol}")
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(funding_rates)
        df['fundingTime'] = pd.to_datetime(df['fundingTime'], unit='ms')
        df['fundingRate'] = df['fundingRate'].astype(float)

        df = df[['fundingTime', 'fundingRate']].rename(columns={
            'fundingTime': 'timestamp',
            'fundingRate': 'funding_rate'
        })

        df.set_index('timestamp', inplace=True)

        logger.info(f"✅ {len(df)} funding rate records | {df.index[0]} → {df.index[-1]}")
        return df

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return pd.DataFrame()


def merge_price_and_funding(price_df: pd.DataFrame, funding_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge 1h price data with 8h funding rate data

    Strategy:
    - Forward-fill funding rates to 1h granularity
    - Each funding rate applies for 8 hours until next update
    """
    logger.info("🔄 Merging price and funding data...")

    # Resample funding to 1h and forward-fill
    funding_1h = funding_df.resample('1h').ffill()

    # Merge with price data
    merged = price_df.join(funding_1h, how='left')

    # Forward-fill any remaining NaN (at the start)
    merged['funding_rate'] = merged['funding_rate'].ffill()

    # Backfill very start if needed
    merged['funding_rate'] = merged['funding_rate'].bfill()

    logger.info(f"✅ Merged {len(merged)} rows")
    logger.info(f"   Funding rate coverage: {merged['funding_rate'].notna().sum()} / {len(merged)}")

    return merged


def main():
    symbol = "BTCUSDT"

    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=365)  # 12 months

    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    logger.info("="*70)
    logger.info("📊 FUNDING RATE DATA DOWNLOAD")
    logger.info("="*70)
    logger.info(f"Symbol: {symbol}")
    logger.info(f"Period: {start_dt} → {end_dt}")
    logger.info("="*70)

    # 1. Download funding rates
    df_funding = download_funding_rate_history(symbol, start_dt, end_dt)

    if df_funding.empty:
        logger.error("❌ Failed to download funding rate data")
        return

    # 2. Load existing 1h price data
    price_file = data_dir / f"{symbol}_1h_12M.parquet"

    if not price_file.exists():
        logger.error(f"❌ Price data not found: {price_file}")
        logger.info("💡 Run download_data_12m.py first to get price data")
        return

    df_price = pd.read_parquet(price_file)
    logger.info(f"✅ Loaded price data: {len(df_price)} 1h candles")

    # 3. Merge
    df_merged = merge_price_and_funding(df_price, df_funding)

    # 4. Save
    output_file = data_dir / f"{symbol}_1h_with_funding_12M.parquet"
    df_merged.to_parquet(output_file)

    logger.info(f"\n💾 Saved: {output_file}")
    logger.info(f"   Rows: {len(df_merged)}")
    logger.info(f"   Columns: {list(df_merged.columns)}")
    logger.info(f"   Date range: {df_merged.index[0]} → {df_merged.index[-1]}")

    # Quick stats
    logger.info(f"\n📊 FUNDING RATE STATS:")
    logger.info(f"   Mean: {df_merged['funding_rate'].mean()*100:.4f}%")
    logger.info(f"   Median: {df_merged['funding_rate'].median()*100:.4f}%")
    logger.info(f"   Min: {df_merged['funding_rate'].min()*100:.4f}%")
    logger.info(f"   Max: {df_merged['funding_rate'].max()*100:.4f}%")
    logger.info(f"   Std: {df_merged['funding_rate'].std()*100:.4f}%")

    logger.info("\n" + "="*70)
    logger.info("✅ FUNDING RATE DOWNLOAD COMPLETE")
    logger.info("="*70)


if __name__ == "__main__":
    main()
