#!/usr/bin/env python3
"""
Market Scanner - ماسح السوق الشامل
يفحص جميع عملات Binance Futures ويختار أفضل الفرص

الاستخدام:
  python3 trading/market_scanner.py --scan          # مسح كامل
  python3 trading/market_scanner.py --top 10        # أفضل 10
  python3 trading/market_scanner.py --continuous    # مسح مستمر
"""

import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime
import json
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

try:
    from binance.client import Client
    from binance.enums import *
except ImportError:
    logger.warning("python-binance not installed. Install: pip install python-binance")
    Client = None


class MarketScanner:
    """ماسح السوق الشامل"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        if Client:
            self.client = Client(api_key or "", api_secret or "")
        else:
            self.client = None
            logger.warning("Binance client not available")
        
        self.cache_file = Path(__file__).parent.parent / 'data' / 'market_scan_cache.json'
        self.cache_file.parent.mkdir(exist_ok=True)
    
    def get_all_futures_symbols(self) -> List[str]:
        """جلب جميع رموز Futures USDT"""
        if not self.client:
            # Fallback: most common symbols
            return [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT',
                'XRPUSDT', 'DOGEUSDT', 'DOTUSDT', 'AVAXUSDT', 'MATICUSDT',
                'LINKUSDT', 'UNIUSDT', 'ATOMUSDT', 'LTCUSDT', 'NEARUSDT',
                'APTUSDT', 'ARBUSDT', 'OPUSDT', 'SUIUSDT', 'INJUSDT'
            ]
        
        try:
            exchange_info = self.client.futures_exchange_info()
            symbols = [
                s['symbol'] for s in exchange_info['symbols']
                if s['symbol'].endswith('USDT') and s['status'] == 'TRADING'
            ]
            logger.info(f"✅ Found {len(symbols)} active USDT futures symbols")
            return symbols
        except Exception as e:
            logger.error(f"❌ Error fetching symbols: {e}")
            return []
    
    def calculate_opportunity_score(self, symbol: str, klines: list) -> Dict:
        """حساب درجة الفرصة"""
        if not klines or len(klines) < 20:
            return None
        
        try:
            # Extract data
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            
            current_price = closes[-1]
            prev_price = closes[-2]
            
            # 1. التغير في السعر (Price Change)
            price_change_pct = ((current_price - prev_price) / prev_price) * 100
            
            # 2. التقلب (Volatility) - أخر 20 شمعة
            volatility = (max(closes[-20:]) - min(closes[-20:])) / min(closes[-20:]) * 100
            
            # 3. الحجم (Volume Surge)
            avg_volume = sum(volumes[-20:-1]) / 19
            current_volume = volumes[-1]
            volume_surge = (current_volume / avg_volume) if avg_volume > 0 else 1
            
            # 4. الزخم (Momentum)
            ma_20 = sum(closes[-20:]) / 20
            momentum = ((current_price - ma_20) / ma_20) * 100
            
            # 5. ATR (Average True Range)
            atr_values = []
            for i in range(1, min(15, len(klines))):
                high_low = highs[-i] - lows[-i]
                high_close = abs(highs[-i] - closes[-i-1])
                low_close = abs(lows[-i] - closes[-i-1])
                true_range = max(high_low, high_close, low_close)
                atr_values.append(true_range)
            
            atr = sum(atr_values) / len(atr_values) if atr_values else 0
            atr_pct = (atr / current_price) * 100 if current_price > 0 else 0
            
            # Opportunity Score Calculation
            score = 0
            reasons = []
            
            # High volatility (good for scalping)
            if volatility > 5:
                score += 25
                reasons.append(f"High volatility: {volatility:.1f}%")
            elif volatility > 3:
                score += 15
                reasons.append(f"Medium volatility: {volatility:.1f}%")
            
            # Volume surge
            if volume_surge > 2:
                score += 30
                reasons.append(f"Volume surge: {volume_surge:.1f}x")
            elif volume_surge > 1.5:
                score += 20
                reasons.append(f"Increased volume: {volume_surge:.1f}x")
            
            # Strong momentum
            if abs(momentum) > 2:
                score += 25
                reasons.append(f"Strong momentum: {momentum:+.1f}%")
            elif abs(momentum) > 1:
                score += 15
                reasons.append(f"Momentum: {momentum:+.1f}%")
            
            # Good ATR (tradeable range)
            if 2 < atr_pct < 8:
                score += 20
                reasons.append(f"Good ATR: {atr_pct:.2f}%")
            
            return {
                'symbol': symbol,
                'score': score,
                'price': current_price,
                'change_24h': price_change_pct,
                'volatility': volatility,
                'volume_surge': volume_surge,
                'momentum': momentum,
                'atr_pct': atr_pct,
                'reasons': reasons
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def scan_market(self, top_n: int = 20) -> List[Dict]:
        """مسح السوق واختيار أفضل الفرص"""
        logger.info(f"\n{'='*70}")
        logger.info("🔍 MARKET SCAN STARTED")
        logger.info(f"{'='*70}\n")
        
        # 1. Get all symbols
        symbols = self.get_all_futures_symbols()
        logger.info(f"📊 Scanning {len(symbols)} symbols...")
        
        if not self.client:
            logger.warning("⚠️  No Binance client - using cached data or simulation")
            return self._get_cached_opportunities(top_n)
        
        # 2. Analyze each symbol
        opportunities = []
        
        for i, symbol in enumerate(symbols, 1):
            try:
                # Get 1h klines (last 24 hours)
                klines = self.client.futures_klines(
                    symbol=symbol,
                    interval=Client.KLINE_INTERVAL_1HOUR,
                    limit=24
                )
                
                result = self.calculate_opportunity_score(symbol, klines)
                if result and result['score'] > 0:
                    opportunities.append(result)
                
                if i % 20 == 0:
                    logger.info(f"   Progress: {i}/{len(symbols)} symbols scanned")
                
            except Exception as e:
                logger.debug(f"Skip {symbol}: {e}")
                continue
        
        # 3. Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        # 4. Cache results
        self._cache_opportunities(opportunities)
        
        # 5. Return top N
        top_opportunities = opportunities[:top_n]
        
        logger.info(f"\n✅ Scan complete! Found {len(opportunities)} opportunities")
        logger.info(f"🏆 Top {len(top_opportunities)} selected\n")
        
        return top_opportunities
    
    def print_opportunities(self, opportunities: List[Dict]):
        """عرض الفرص بشكل جميل"""
        print(f"\n{'='*100}")
        print(f"🏆 TOP TRADING OPPORTUNITIES")
        print(f"{'='*100}\n")
        
        print(f"{'#':>3} | {'Symbol':<12} | {'Score':>5} | {'Price':>12} | {'24h %':>8} | {'Vol':>6} | {'Reason'}")
        print(f"{'-'*100}")
        
        for i, opp in enumerate(opportunities, 1):
            reasons_str = ", ".join(opp['reasons'][:2])  # First 2 reasons
            
            print(
                f"{i:>3} | "
                f"{opp['symbol']:<12} | "
                f"{opp['score']:>5.0f} | "
                f"${opp['price']:>11,.2f} | "
                f"{opp['change_24h']:>7.2f}% | "
                f"{opp['volume_surge']:>5.1f}x | "
                f"{reasons_str}"
            )
        
        print(f"\n{'='*100}\n")
    
    def _cache_opportunities(self, opportunities: List[Dict]):
        """حفظ النتائج في cache"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'opportunities': opportunities
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Cache write error: {e}")
    
    def _get_cached_opportunities(self, top_n: int) -> List[Dict]:
        """جلب من cache"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    opportunities = cache_data.get('opportunities', [])
                    logger.info(f"📋 Using cached data from {cache_data.get('timestamp')}")
                    return opportunities[:top_n]
        except:
            pass
        
        return []
    
    async def continuous_scan(self, interval: int = 3600, top_n: int = 20):
        """مسح مستمر كل ساعة"""
        logger.info(f"🔄 Starting continuous market scan (every {interval}s)...\n")
        
        while True:
            try:
                opportunities = self.scan_market(top_n)
                self.print_opportunities(opportunities)
                
                logger.info(f"💤 Sleeping for {interval}s ({interval//60}min)...\n")
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Scan stopped")
                break
            except Exception as e:
                logger.error(f"❌ Error in continuous scan: {e}")
                await asyncio.sleep(60)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Market Scanner')
    parser.add_argument('--scan', action='store_true', help='Scan market once')
    parser.add_argument('--top', type=int, default=20, help='Top N opportunities')
    parser.add_argument('--continuous', action='store_true', help='Continuous scanning')
    parser.add_argument('--interval', type=int, default=3600, help='Scan interval (seconds)')
    
    args = parser.parse_args()
    
    scanner = MarketScanner()
    
    if args.continuous:
        await scanner.continuous_scan(interval=args.interval, top_n=args.top)
    else:
        opportunities = scanner.scan_market(top_n=args.top)
        scanner.print_opportunities(opportunities)


if __name__ == '__main__':
    asyncio.run(main())
