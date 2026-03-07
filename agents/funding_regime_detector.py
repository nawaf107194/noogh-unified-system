#!/usr/bin/env python3
"""
Funding Rate Regime Detector
==============================
Detects when market is in HIGH FUNDING regime (deploy capital)
vs LOW/NEGATIVE regime (stay out)

Strategy:
- Monitor 20+ symbols daily
- Alert when ANY symbol enters HIGH FUNDING regime
- Deploy capital opportunistically (not always-on)
- Exit when funding normalizes

Regime Classification:
- 🔥 HOT: 3-day avg > 0.10% daily (60%+ APR potential)
- ⚠️  WARM: 3-day avg > 0.04% daily (24%+ APR)
- 🟢 NEUTRAL: -0.04% to +0.04% daily
- ❄️  COLD: < -0.04% daily (inverse arb opportunity)
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from binance.client import Client
import json

API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")


class FundingRegimeDetector:
    """Detect funding rate regimes across multiple symbols"""

    def __init__(self):
        self.client = Client(API_KEY, API_SECRET)

        # Extended symbol list (focus on high-beta altcoins)
        self.symbols = [
            # Majors
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT',
            # High Beta L1s
            'SOLUSDT', 'AVAXUSDT', 'NEARUSDT', 'APTUSDT', 'SUIUSDT',
            # High Beta Alts
            'DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT', 'FLOKIUSDT',
            'LINKUSDT', 'ADAUSDT', 'DOTUSDT', 'MATICUSDT', 'ATOMUSDT',
            # DeFi
            'AAVEUSDT', 'UNIUSDT', 'CRVUSDT',
            # Gaming/Metaverse
            'AXSUSDT', 'SANDUSDT', 'MANAUSDT',
            # New Narratives
            'INJUSDT', 'TIAUSDT', 'WLDUSDT', 'RENDERUSDT'
        ]

        # Regime thresholds
        self.REGIME_HOT = 0.0010  # 0.10% daily = 60%+ APR
        self.REGIME_WARM = 0.0004  # 0.04% daily = 24%+ APR
        self.REGIME_NEUTRAL = 0.0001  # ±0.01% daily

    def get_funding_history(self, symbol: str, days: int = 7) -> pd.DataFrame:
        """Get recent funding history"""
        try:
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

            rates = self.client.futures_funding_rate(
                symbol=symbol,
                startTime=start_time,
                endTime=end_time,
                limit=1000
            )

            if not rates:
                return pd.DataFrame()

            df = pd.DataFrame(rates)
            df['fundingTime'] = pd.to_datetime(df['fundingTime'], unit='ms')
            df['fundingRate'] = df['fundingRate'].astype(float)
            df = df[['fundingTime', 'fundingRate']].set_index('fundingTime')

            return df

        except Exception as e:
            return pd.DataFrame()

    def classify_regime(self, avg_funding_daily: float) -> dict:
        """Classify funding regime"""
        if avg_funding_daily >= self.REGIME_HOT:
            return {
                'regime': 'HOT',
                'emoji': '🔥',
                'action': 'DEPLOY CAPITAL',
                'apr_estimate': f"{avg_funding_daily * 365 * 100:.0f}%"
            }
        elif avg_funding_daily >= self.REGIME_WARM:
            return {
                'regime': 'WARM',
                'emoji': '⚠️ ',
                'action': 'Consider entry',
                'apr_estimate': f"{avg_funding_daily * 365 * 100:.0f}%"
            }
        elif avg_funding_daily <= -self.REGIME_HOT:
            return {
                'regime': 'INVERSE_HOT',
                'emoji': '❄️🔥',
                'action': 'INVERSE ARB (short spot + long perp)',
                'apr_estimate': f"{abs(avg_funding_daily) * 365 * 100:.0f}%"
            }
        elif avg_funding_daily <= -self.REGIME_WARM:
            return {
                'regime': 'INVERSE_WARM',
                'emoji': '❄️ ',
                'action': 'Consider inverse entry',
                'apr_estimate': f"{abs(avg_funding_daily) * 365 * 100:.0f}%"
            }
        else:
            return {
                'regime': 'NEUTRAL',
                'emoji': '🟢',
                'action': 'WAIT',
                'apr_estimate': 'N/A'
            }

    def scan_all_regimes(self) -> pd.DataFrame:
        """Scan all symbols and classify regimes"""
        print("="*70)
        print("🌡️  FUNDING RATE REGIME DETECTOR")
        print("="*70)
        print(f"\nScanning {len(self.symbols)} symbols...")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")

        results = []

        for symbol in self.symbols:
            # Get last 7 days funding
            hist = self.get_funding_history(symbol, days=7)

            if hist.empty:
                continue

            # Calculate 3-day average (last 9 funding periods)
            recent = hist['fundingRate'].tail(9)
            avg_funding_8h = recent.mean()
            avg_funding_daily = avg_funding_8h * 3

            # Calculate 7-day stats
            avg_7d = hist['fundingRate'].mean() * 3
            std_7d = hist['fundingRate'].std() * 3

            # Check if sustained (7 of 9 same sign)
            positive_count = (recent > 0).sum()
            sustained = positive_count >= 7 or positive_count <= 2

            # Classify regime
            regime = self.classify_regime(avg_funding_daily)

            results.append({
                'symbol': symbol,
                'regime': regime['regime'],
                'emoji': regime['emoji'],
                'action': regime['action'],
                'avg_3d_daily': avg_funding_daily,
                'avg_7d_daily': avg_7d,
                'volatility': std_7d,
                'sustained': sustained,
                'apr_estimate': regime['apr_estimate']
            })

        df = pd.DataFrame(results)
        df = df.sort_values('avg_3d_daily', ascending=False)

        return df

    def print_regime_report(self, df: pd.DataFrame):
        """Print formatted regime report"""
        print("="*70)
        print("📊 REGIME ANALYSIS")
        print("="*70)

        # Group by regime
        hot = df[df['regime'] == 'HOT']
        warm = df[df['regime'] == 'WARM']
        inverse_hot = df[df['regime'] == 'INVERSE_HOT']
        inverse_warm = df[df['regime'] == 'INVERSE_WARM']
        neutral = df[df['regime'] == 'NEUTRAL']

        print(f"\n🔥 HOT REGIME ({len(hot)} symbols) - DEPLOY NOW!")
        if len(hot) > 0:
            for _, row in hot.iterrows():
                print(f"   {row['emoji']} {row['symbol']:12s} | {row['avg_3d_daily']*100:+.4f}% daily | APR: {row['apr_estimate']}")
        else:
            print("   (None)")

        print(f"\n⚠️  WARM REGIME ({len(warm)} symbols) - Consider")
        if len(warm) > 0:
            for _, row in warm.iterrows():
                print(f"   {row['emoji']} {row['symbol']:12s} | {row['avg_3d_daily']*100:+.4f}% daily | APR: {row['apr_estimate']}")
        else:
            print("   (None)")

        print(f"\n❄️🔥 INVERSE HOT ({len(inverse_hot)} symbols) - SHORT SPOT + LONG PERP")
        if len(inverse_hot) > 0:
            for _, row in inverse_hot.iterrows():
                print(f"   {row['emoji']} {row['symbol']:12s} | {row['avg_3d_daily']*100:+.4f}% daily | APR: {row['apr_estimate']}")
        else:
            print("   (None)")

        print(f"\n❄️  INVERSE WARM ({len(inverse_warm)} symbols) - Consider Inverse")
        if len(inverse_warm) > 0:
            for _, row in inverse_warm.iterrows():
                print(f"   {row['emoji']} {row['symbol']:12s} | {row['avg_3d_daily']*100:+.4f}% daily | APR: {row['apr_estimate']}")
        else:
            print("   (None)")

        print(f"\n🟢 NEUTRAL ({len(neutral)} symbols) - No opportunity")

        # Market summary
        print(f"\n{'='*70}")
        print(f"🎯 MARKET SUMMARY")
        print(f"{'='*70}")

        total_hot = len(hot) + len(inverse_hot)
        total_warm = len(warm) + len(inverse_warm)

        if total_hot > 0:
            print(f"\n✅ ACTIVE MARKET - {total_hot} symbols in HOT regime")
            print(f"   💰 Capital deployment recommended")
            print(f"   🎯 Expected returns: 40-200% APR")
        elif total_warm > 0:
            print(f"\n⚠️  MODERATE MARKET - {total_warm} symbols in WARM regime")
            print(f"   Consider selective deployment")
            print(f"   Expected returns: 15-40% APR")
        else:
            print(f"\n❌ DEAD MARKET - No funding opportunities")
            print(f"   WAIT for regime shift")
            print(f"   Current market: Consolidation/Bear")

        # Save results
        output_file = Path(__file__).parent.parent / 'data' / 'funding_regimes.csv'
        df.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file.name}")


def main():
    detector = FundingRegimeDetector()
    df = detector.scan_all_regimes()
    detector.print_regime_report(df)


if __name__ == "__main__":
    main()
