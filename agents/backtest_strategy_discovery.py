#!/usr/bin/env python3
"""
Backtest-based Strategy Discovery Engine
يحلل historical data لاستخراج patterns وإنشاء استراتيجيات جديدة

الهدف:
- جمع 10,000+ setups من historical data
- Brain يحلل كل setup
- استخراج patterns تحسّن WR و PF
- توليد strategy rules جديدة
"""
import sys
import asyncio
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging
from typing import List, Dict
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading.binance_futures import BinanceFuturesManager
from trading.trap_hybrid_engine import get_trap_hybrid_engine
from unified_core.neural_bridge import NeuralEngineClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


class BacktestStrategyDiscovery:
    """محرك اكتشاف الاستراتيجيات من البيانات التاريخية"""

    def __init__(self, neural_bridge=None):
        self.neural_bridge = neural_bridge
        # Use PRODUCTION for historical data (read-only, safe)
        self.binance = BinanceFuturesManager(testnet=False, read_only=True)
        self.trap_engine = get_trap_hybrid_engine()

        # Storage
        self.setups = []
        self.patterns = defaultdict(list)
        self.discoveries = []

        logger.info("🔬 Backtest Strategy Discovery initialized")

    async def fetch_historical_data(
        self,
        symbol: str,
        days: int = 180,
        interval: str = '5m'
    ) -> pd.DataFrame:
        """جلب بيانات تاريخية"""
        logger.info(f"📥 Fetching {days} days of {interval} data for {symbol}...")

        try:
            # Binance limit: 1500 candles per request
            # 5m: 1500 candles = ~5 days
            all_data = []

            end_time = int(datetime.now().timestamp() * 1000)  # Convert to milliseconds

            while days > 0:
                batch_days = min(days, 5)
                start_time = end_time - (batch_days * 24 * 60 * 60 * 1000)  # milliseconds

                # Fetch historical batch using startTime and endTime
                klines = self.binance.client.futures_klines(
                    symbol=symbol,
                    interval=interval,
                    startTime=start_time,
                    endTime=end_time,
                    limit=1500
                )

                if klines:
                    # Convert to DataFrame (same format as get_klines())
                    df = pd.DataFrame(klines, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades',
                        'taker_buy_base', 'taker_buy_quote', 'ignore'
                    ])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    for col in ['open', 'high', 'low', 'close', 'volume', 'taker_buy_base']:
                        df[col] = df[col].astype(float)
                    df.set_index('timestamp', inplace=True)

                    all_data.append(df)
                    logger.info(f"   ✅ Fetched {len(df)} candles ({df.index[0].date()} to {df.index[-1].date()})")

                end_time = start_time
                days -= batch_days

            if all_data:
                combined = pd.concat(all_data, ignore_index=False)
                combined = combined.sort_index()
                logger.info(f"✅ Total: {len(combined)} candles")

                # Debug: Check data quality
                logger.info(f"   Sample data: Close range [{combined['close'].min():.2f}, {combined['close'].max():.2f}]")
                logger.info(f"   Has taker_buy_base: {'taker_buy_base' in combined.columns}")
                if 'taker_buy_base' in combined.columns:
                    logger.info(f"   Taker buy ratio: {(combined['taker_buy_base'].sum() / combined['volume'].sum() * 100):.1f}%")

                return combined

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"❌ Error fetching data: {e}")
            return pd.DataFrame()

    async def analyze_historical_setups(
        self,
        symbol: str,
        days: int = 30
    ) -> List[Dict]:
        """تحليل setups تاريخية وجمع بيانات"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 Analyzing {symbol} - Last {days} days")
        logger.info(f"{'='*60}")

        # Fetch data
        df = await self.fetch_historical_data(symbol, days=days)

        if df.empty:
            logger.warning(f"⚠️ No data for {symbol}")
            return []

        # Compute indicators
        df = self.trap_engine.compute_indicators(df)

        # Debug: Check if indicators were computed
        logger.info(f"   Indicators computed: ATR mean={df['atr'].mean():.4f}, Delta mean={df['delta'].mean():.2f}")
        logger.info(f"   Bull sweeps: {df['bull_sweep'].sum()}, Bear sweeps: {df['bear_sweep'].sum()}")
        logger.info(f"   Long signals: {df.get('long_signal', pd.Series()).sum()}, Short signals: {df.get('short_signal', pd.Series()).sum()}")

        # Scan for setups
        setups_found = []

        for i in range(100, len(df) - 50):  # Leave buffer for outcome
            signal = self.trap_engine.generate_signal(df, current_idx=i)

            # Debug: Log first few signals to see what's happening
            if i < 105 or signal.signal != 'NONE':
                logger.debug(f"   Index {i}: Signal={signal.signal}, Reasons={signal.reasons}")

            if signal.signal == 'NONE':
                continue

            # Calculate outcome (50 candles forward)
            entry_price = signal.entry_price
            stop_loss = signal.stop_loss
            take_profit = signal.quick_tp

            # Check what happened in next 50 candles
            future_slice = df.iloc[i+1:i+51]

            hit_tp = False
            hit_sl = False
            max_profit = 0
            max_loss = 0

            for _, bar in future_slice.iterrows():
                h, l = bar['high'], bar['low']

                if signal.signal == 'LONG':
                    profit_pct = ((h - entry_price) / entry_price) * 100
                    loss_pct = ((l - entry_price) / entry_price) * 100

                    if h >= take_profit:
                        hit_tp = True
                        break
                    if l <= stop_loss:
                        hit_sl = True
                        break

                    max_profit = max(max_profit, profit_pct)
                    max_loss = min(max_loss, loss_pct)

                else:  # SHORT
                    profit_pct = ((entry_price - l) / entry_price) * 100
                    loss_pct = ((entry_price - h) / entry_price) * 100

                    if l <= take_profit:
                        hit_tp = True
                        break
                    if h >= stop_loss:
                        hit_sl = True
                        break

                    max_profit = max(max_profit, profit_pct)
                    max_loss = min(max_loss, loss_pct)

            # Determine outcome
            if hit_tp:
                outcome = 'WIN'
            elif hit_sl:
                outcome = 'LOSS'
            else:
                outcome = 'TIMEOUT'

            # Extract features
            bar = df.iloc[i]
            setup = {
                'timestamp': bar.name,
                'symbol': symbol,
                'signal': signal.signal,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'atr': signal.atr,
                'reasons': signal.reasons,
                'outcome': outcome,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'hit_tp': hit_tp,
                'hit_sl': hit_sl,
                # Features
                'rsi': bar.get('rsi', 50),
                'volume': bar.get('volume', 0),
                'taker_buy_ratio': bar.get('taker_buy_base', 0) / bar.get('volume', 1) if bar.get('volume', 0) > 0 else 0.5,
            }

            setups_found.append(setup)

        logger.info(f"✅ Found {len(setups_found)} setups")

        # Quick stats
        wins = sum(1 for s in setups_found if s['outcome'] == 'WIN')
        losses = sum(1 for s in setups_found if s['outcome'] == 'LOSS')
        wr = (wins / len(setups_found) * 100) if setups_found else 0

        logger.info(f"   Win Rate: {wr:.1f}% ({wins}W / {losses}L)")

        return setups_found

    async def discover_patterns(self, setups: List[Dict]):
        """استخراج patterns من setups"""
        logger.info(f"\n{'='*60}")
        logger.info("🧠 Analyzing patterns...")
        logger.info(f"{'='*60}")

        if not setups:
            logger.warning("⚠️ No setups to analyze")
            return

        # Group by outcome
        wins = [s for s in setups if s['outcome'] == 'WIN']
        losses = [s for s in setups if s['outcome'] == 'LOSS']

        logger.info(f"\nDataset: {len(wins)} wins, {len(losses)} losses")

        # Analyze patterns
        discoveries = []

        # Pattern 1: Reason combinations
        logger.info("\n📊 Pattern 1: Best reason combinations")
        reason_stats = defaultdict(lambda: {'wins': 0, 'losses': 0})

        for s in setups:
            reasons_str = ' + '.join(sorted(s['reasons']))
            if s['outcome'] == 'WIN':
                reason_stats[reasons_str]['wins'] += 1
            elif s['outcome'] == 'LOSS':
                reason_stats[reasons_str]['losses'] += 1

        for reasons, stats in sorted(
            reason_stats.items(),
            key=lambda x: x[1]['wins'] / (x[1]['wins'] + x[1]['losses'] + 0.001),
            reverse=True
        )[:5]:
            total = stats['wins'] + stats['losses']
            wr = (stats['wins'] / total * 100) if total > 0 else 0

            if total >= 3:  # Minimum sample size
                logger.info(f"   {reasons}: {wr:.1f}% WR ({stats['wins']}W/{stats['losses']}L)")

                discoveries.append({
                    'type': 'reason_combination',
                    'pattern': reasons,
                    'win_rate': wr,
                    'sample_size': total
                })

        self.discoveries = discoveries

        # Save discoveries
        output_file = Path('/home/noogh/projects/noogh_unified_system/src/data/pattern_discoveries.json')
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_setups': len(setups),
                'wins': len(wins),
                'losses': len(losses),
                'discoveries': discoveries
            }, f, indent=2)

        logger.info(f"\n💾 Discoveries saved to: {output_file}")

        return discoveries

    async def run_analysis(self, symbols: List[str], days: int = 30):
        """تشغيل التحليل الكامل"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 BACKTEST STRATEGY DISCOVERY")
        logger.info(f"{'='*70}")
        logger.info(f"Symbols: {len(symbols)}")
        logger.info(f"Period: Last {days} days")
        logger.info(f"{'='*70}\n")

        all_setups = []

        for symbol in symbols:
            setups = await self.analyze_historical_setups(symbol, days=days)
            all_setups.extend(setups)

        logger.info(f"\n{'='*70}")
        logger.info(f"📊 TOTAL SETUPS COLLECTED: {len(all_setups)}")
        logger.info(f"{'='*70}\n")

        # Save all setups
        setups_file = Path('/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl')
        setups_file.parent.mkdir(parents=True, exist_ok=True)

        with open(setups_file, 'w') as f:
            for setup in all_setups:
                f.write(json.dumps(setup, default=str) + '\n')

        logger.info(f"💾 Setups saved to: {setups_file}")

        # Discover patterns
        await self.discover_patterns(all_setups)

        logger.info(f"\n{'='*70}")
        logger.info("✅ BACKTEST ANALYSIS COMPLETE")
        logger.info(f"{'='*70}\n")


async def main():
    """نقطة البداية"""

    # Initialize Neural Bridge
    neural_bridge = NeuralEngineClient(
        base_url="http://localhost:11434",
        mode="vllm"
    )

    # Initialize Discovery Engine
    engine = BacktestStrategyDiscovery(neural_bridge=neural_bridge)

    # Top liquid symbols for analysis
    symbols = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
        'ADAUSDT', 'DOGEUSDT', 'MATICUSDT', 'DOTUSDT', 'LTCUSDT'
    ]

    # Run analysis (30 days for speed, can increase later)
    await engine.run_analysis(symbols, days=30)


if __name__ == "__main__":
    asyncio.run(main())
