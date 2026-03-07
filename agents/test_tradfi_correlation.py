#!/usr/bin/env python3
"""
TradFi-Crypto Correlation Test
================================
Test if TradFi moves (Nasdaq, DXY) predict BTC with lag

Hypotheses to test:
1. Nasdaq close → BTC 1-4h later (risk-on correlation)
2. DXY move → BTC inverse 1-4h later (dollar strength inverse)
3. Bond yields → BTC risk-off correlation
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta
from scipy import stats


def download_tradfi_data(start_date: str, end_date: str) -> dict:
    """
    Download TradFi data from Yahoo Finance

    Tickers:
    - ^IXIC: Nasdaq Composite
    - DX-Y.NYB: US Dollar Index
    - ^TNX: 10-Year Treasury Yield
    """
    print("📥 Downloading TradFi data from Yahoo Finance...")

    tickers = {
        'NASDAQ': '^IXIC',
        'DXY': 'DX-Y.NYB',
        'YIELD_10Y': '^TNX'
    }

    data = {}

    for name, ticker in tickers.items():
        try:
            print(f"   Downloading {name} ({ticker})...")
            df = yf.download(ticker, start=start_date, end=end_date, interval='1h', progress=False)

            if df.empty:
                print(f"   ⚠️  No data for {name}, trying daily...")
                df = yf.download(ticker, start=start_date, end=end_date, interval='1d', progress=False)

            if not df.empty:
                # Flatten MultiIndex columns if present
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                # Remove timezone info to match BTC data
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)

                # Keep only Close price
                data[name] = df[['Close']].rename(columns={'Close': name})
                print(f"   ✅ {len(df)} bars")
            else:
                print(f"   ❌ No data available for {name}")
                data[name] = None

        except Exception as e:
            print(f"   ❌ Error downloading {name}: {e}")
            data[name] = None

    return data


def calculate_returns(df: pd.DataFrame, col: str, periods: list = [1, 2, 4, 8]) -> pd.DataFrame:
    """Calculate returns over multiple periods"""
    out = df.copy()

    for p in periods:
        out[f'{col}_ret_{p}h'] = df[col].pct_change(p)

    return out


def test_correlation(btc_df: pd.DataFrame, tradfi_df: pd.DataFrame,
                     btc_col: str, tradfi_col: str, lags: list = [1, 2, 4, 8, 12, 24]) -> pd.DataFrame:
    """
    Test correlation between TradFi and BTC with various lags

    Returns DataFrame with lag, correlation, p-value
    """
    results = []

    # Merge data
    merged = btc_df.join(tradfi_df, how='inner')

    for lag in lags:
        # Shift TradFi data forward (lag)
        # If correlation exists, TradFi_t predicts BTC_{t+lag}
        tradfi_lagged = merged[tradfi_col].shift(lag)

        # Remove NaN
        valid = merged[[btc_col]].join(tradfi_lagged.rename(f'{tradfi_col}_lag{lag}'), how='inner').dropna()

        if len(valid) < 50:
            continue

        # Pearson correlation
        corr, p_value = stats.pearsonr(valid[f'{tradfi_col}_lag{lag}'], valid[btc_col])

        results.append({
            'lag_hours': lag,
            'correlation': corr,
            'p_value': p_value,
            'n_samples': len(valid),
            'significant': p_value < 0.05
        })

    return pd.DataFrame(results)


def main():
    print("="*70)
    print("🔬 TRADFI-CRYPTO CORRELATION TEST")
    print("="*70)

    # Load BTC 1h data
    btc_file = Path(__file__).parent.parent / 'data' / 'BTCUSDT_1h_12M.parquet'

    if not btc_file.exists():
        print(f"❌ BTC data not found: {btc_file}")
        return

    btc_df = pd.read_parquet(btc_file)
    print(f"\n✅ Loaded BTC data: {len(btc_df)} 1h bars")
    print(f"   Date range: {btc_df.index[0]} → {btc_df.index[-1]}")

    # Download TradFi data
    start_date = btc_df.index[0].strftime('%Y-%m-%d')
    end_date = btc_df.index[-1].strftime('%Y-%m-%d')

    tradfi_data = download_tradfi_data(start_date, end_date)

    # Calculate BTC returns
    print(f"\n🔧 Calculating BTC returns...")
    btc_df = calculate_returns(btc_df, 'close', periods=[1, 2, 4, 8])

    print(f"\n{'='*70}")
    print(f"📊 CORRELATION ANALYSIS")
    print(f"{'='*70}")

    # Test 1: Nasdaq → BTC
    if tradfi_data['NASDAQ'] is not None:
        print(f"\n🔍 TEST 1: NASDAQ → BTC correlation")
        print(f"-"*70)

        nasdaq_df = tradfi_data['NASDAQ']

        # Resample to 1h if daily
        if len(nasdaq_df) < 1000:  # Daily data
            print(f"   ⚠️  Nasdaq data is daily, resampling to 1h (forward-fill)...")
            nasdaq_df = nasdaq_df.resample('1h').ffill()

        # Calculate Nasdaq returns
        nasdaq_df = calculate_returns(nasdaq_df, 'NASDAQ', periods=[1, 4, 24])

        # Test correlation: Nasdaq return → BTC return (with lag)
        for nasdaq_ret_period in [1, 4, 24]:
            nasdaq_col = f'NASDAQ_ret_{nasdaq_ret_period}h'

            if nasdaq_col not in nasdaq_df.columns:
                continue

            print(f"\n   Testing: {nasdaq_col} → BTC_ret_1h (with lag)")

            results = test_correlation(
                btc_df[['close_ret_1h']],
                nasdaq_df[[nasdaq_col]],
                'close_ret_1h',
                nasdaq_col,
                lags=[1, 2, 4, 8, 12, 24]
            )

            if len(results) > 0:
                # Sort by absolute correlation
                results = results.sort_values('correlation', key=abs, ascending=False)

                print(f"\n   Top correlations:")
                for _, row in results.head(3).iterrows():
                    sig = "✅" if row['significant'] else "  "
                    print(f"   {sig} Lag {row['lag_hours']:2d}h: r={row['correlation']:+.3f}, p={row['p_value']:.4f}, n={row['n_samples']}")

    # Test 2: DXY → BTC (inverse correlation expected)
    if tradfi_data['DXY'] is not None:
        print(f"\n🔍 TEST 2: DXY → BTC inverse correlation")
        print(f"-"*70)

        dxy_df = tradfi_data['DXY']

        # Resample to 1h if daily
        if len(dxy_df) < 1000:
            print(f"   ⚠️  DXY data is daily, resampling to 1h (forward-fill)...")
            dxy_df = dxy_df.resample('1h').ffill()

        # Calculate DXY returns
        dxy_df = calculate_returns(dxy_df, 'DXY', periods=[1, 4, 24])

        # Test correlation
        for dxy_ret_period in [1, 4, 24]:
            dxy_col = f'DXY_ret_{dxy_ret_period}h'

            if dxy_col not in dxy_df.columns:
                continue

            print(f"\n   Testing: {dxy_col} → BTC_ret_1h (expecting negative correlation)")

            results = test_correlation(
                btc_df[['close_ret_1h']],
                dxy_df[[dxy_col]],
                'close_ret_1h',
                dxy_col,
                lags=[1, 2, 4, 8, 12, 24]
            )

            if len(results) > 0:
                results = results.sort_values('correlation', key=abs, ascending=False)

                print(f"\n   Top correlations:")
                for _, row in results.head(3).iterrows():
                    sig = "✅" if row['significant'] else "  "
                    print(f"   {sig} Lag {row['lag_hours']:2d}h: r={row['correlation']:+.3f}, p={row['p_value']:.4f}, n={row['n_samples']}")

    # Test 3: 10Y Yield → BTC
    if tradfi_data['YIELD_10Y'] is not None:
        print(f"\n🔍 TEST 3: 10Y Treasury Yield → BTC correlation")
        print(f"-"*70)

        yield_df = tradfi_data['YIELD_10Y']

        # Resample to 1h if daily
        if len(yield_df) < 1000:
            print(f"   ⚠️  Yield data is daily, resampling to 1h (forward-fill)...")
            yield_df = yield_df.resample('1h').ffill()

        # Calculate yield changes
        yield_df = calculate_returns(yield_df, 'YIELD_10Y', periods=[1, 4, 24])

        # Test correlation
        for yield_ret_period in [1, 4, 24]:
            yield_col = f'YIELD_10Y_ret_{yield_ret_period}h'

            if yield_col not in yield_df.columns:
                continue

            print(f"\n   Testing: {yield_col} → BTC_ret_1h")

            results = test_correlation(
                btc_df[['close_ret_1h']],
                yield_df[[yield_col]],
                'close_ret_1h',
                yield_col,
                lags=[1, 2, 4, 8, 12, 24]
            )

            if len(results) > 0:
                results = results.sort_values('correlation', key=abs, ascending=False)

                print(f"\n   Top correlations:")
                for _, row in results.head(3).iterrows():
                    sig = "✅" if row['significant'] else "  "
                    print(f"   {sig} Lag {row['lag_hours']:2d}h: r={row['correlation']:+.3f}, p={row['p_value']:.4f}, n={row['n_samples']}")

    print(f"\n{'='*70}")
    print(f"🎯 VERDICT:")
    print(f"{'='*70}")
    print(f"""
If any correlation shows:
- ✅ |r| > 0.1 (weak but tradeable)
- ✅ p < 0.05 (statistically significant)
- ✅ Consistent across multiple lags
→ Worth building predictive model

Otherwise:
→ TradFi correlation hypothesis REJECTED
    """)
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
