#!/usr/bin/env python3
"""
Signal Engine V3 - محرك الإشارات v3

يدمج:
1. Market Scanner (اختيار العملات)
2. Technical Analyzer (التحليل الفني)
3. Risk Calculator (حساب SL/TP)
4. Database (حفظ الإشارات)

النتيجة: إشارة كاملة جاهزة للتنفيذ
"""

import sys
import logging
import pandas as pd
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from trading.market_scanner import MarketScanner
except ImportError:
    MarketScanner = None

try:
    from trading.technical_analyzer import TechnicalAnalyzer
except ImportError:
    TechnicalAnalyzer = None

try:
    from data import TradeRepository, MarketDataRepository
    from data.models import Signal
except ImportError:
    logger.warning("⚠️ Data layer not available")
    TradeRepository = None
    Signal = None

try:
    from binance.client import Client
except ImportError:
    Client = None


class SignalEngineV3:
    """محرك إشارات متكامل"""
    
    VERSION = "3.0.0"
    
    def __init__(self, client=None, config: Dict = None):
        self.client = client
        self.config = config or self._default_config()
        
        # Initialize components
        self.scanner = MarketScanner() if MarketScanner else None
        self.technical = TechnicalAnalyzer() if TechnicalAnalyzer else None
        self.market_data_repo = MarketDataRepository() if MarketDataRepository else None
        
        logger.info(f"🚀 Signal Engine V3 initialized (v{self.VERSION})")
    
    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            'min_technical_score': 70,
            'min_confidence': 75,
            'stop_loss_pct': 3.0,
            'take_profit_pct': 7.5,
            'use_atr_for_sl': False,  # Future: adaptive SL based on ATR
            'timeframe': '1h',
            'lookback_candles': 100
        }
    
    def get_market_data(self, symbol: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """جلب بيانات السوق"""
        # Try database first
        if self.market_data_repo:
            df = self.market_data_repo.get_ohlcv(
                symbol=symbol,
                timeframe=self.config['timeframe'],
                limit=limit
            )
            if not df.empty:
                return df
        
        # Fallback to API
        if not self.client:
            logger.warning(f"⚠️ No data source for {symbol}")
            return None
        
        try:
            klines = self.client.futures_klines(
                symbol=symbol,
                interval=self.config['timeframe'],
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"❌ Error fetching data for {symbol}: {e}")
            return None
    
    def analyze(self, symbol: str, save_to_db: bool = True) -> Optional[Dict]:
        """تحليل كامل للعملة"""
        logger.info(f"🔍 Analyzing {symbol}...")
        
        # 1. Get market data
        df = self.get_market_data(symbol, self.config['lookback_candles'])
        if df is None or len(df) < 100:
            logger.warning(f"⚠️ Insufficient data for {symbol}")
            return None
        
        # 2. Technical analysis
        if not self.technical:
            logger.error("❌ Technical Analyzer not available")
            return None
        
        tech_analysis = self.technical.analyze(df, symbol=symbol)
        
        if 'error' in tech_analysis:
            logger.warning(f"⚠️ {symbol}: {tech_analysis['error']}")
            return None
        
        # 3. Build signal
        signal = self._build_signal(symbol, df, tech_analysis)
        
        # 4. Validate signal
        is_valid, reason = self._validate_signal(signal)
        if not is_valid:
            signal['action'] = 'SKIPPED'
            signal['skip_reason'] = reason
            logger.info(f"❌ {symbol}: {reason}")
        else:
            signal['action'] = 'READY'
            logger.info(f"✅ {symbol}: Signal READY (Score: {signal['technical_score']})")
        
        # 5. Save to database
        if save_to_db and Signal:
            self._save_signal(signal)
        
        return signal
    
    def _build_signal(self, symbol: str, df: pd.DataFrame, tech_analysis: Dict) -> Dict:
        """بناء إشارة"""
        current_price = df['close'].iloc[-1]
        
        # Direction from technical analysis
        direction = tech_analysis['signal']['direction']
        confidence_level = tech_analysis['signal']['confidence']
        
        # Map confidence to numeric
        confidence_map = {'HIGH': 90, 'MEDIUM': 75, 'LOW': 50}
        confidence = confidence_map.get(confidence_level, 50)
        
        # Calculate SL/TP
        sl_pct = self.config['stop_loss_pct']
        tp_pct = self.config['take_profit_pct']
        
        if direction == 'LONG':
            sl_price = current_price * (1 - sl_pct / 100)
            tp_price = current_price * (1 + tp_pct / 100)
        elif direction == 'SHORT':
            sl_price = current_price * (1 + sl_pct / 100)
            tp_price = current_price * (1 - tp_pct / 100)
        else:  # NEUTRAL
            sl_price = None
            tp_price = None
        
        # Extract key indicators
        indicators = tech_analysis.get('indicators', {})
        patterns = tech_analysis.get('candlestick_patterns', {}).get('patterns', [])
        sr = tech_analysis.get('support_resistance', {})
        trend = tech_analysis.get('trend', {})
        
        signal = {
            'symbol': symbol,
            'timestamp': datetime.utcnow(),
            'direction': direction,
            'confidence': confidence,
            'entry_price': current_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'technical_score': tech_analysis['technical_score'],
            'rsi': indicators.get('rsi'),
            'macd_signal': indicators.get('macd_signal'),
            'ma_signal': indicators.get('ma_signal'),
            'patterns': patterns,
            'support_resistance': sr,
            'trend_strength': trend.get('trend_strength'),
            'volatility': None,  # TODO: from market scanner
            'volume_surge': None,  # TODO: from market scanner
            'engine_version': self.VERSION,
            'full_analysis': tech_analysis
        }
        
        return signal
    
    def _validate_signal(self, signal: Dict) -> tuple[bool, str]:
        """فحص صحة الإشارة"""
        # 1. Check technical score
        if signal['technical_score'] < self.config['min_technical_score']:
            return False, f"Low tech score: {signal['technical_score']} < {self.config['min_technical_score']}"
        
        # 2. Check confidence
        if signal['confidence'] < self.config['min_confidence']:
            return False, f"Low confidence: {signal['confidence']} < {self.config['min_confidence']}"
        
        # 3. Check direction
        if signal['direction'] == 'NEUTRAL':
            return False, "No clear direction"
        
        # 4. Check SL/TP exist
        if signal['sl_price'] is None or signal['tp_price'] is None:
            return False, "SL/TP not calculated"
        
        return True, "Valid"
    
    def _save_signal(self, signal: Dict):
        """حفظ الإشارة في قاعدة البيانات"""
        try:
            from data.database import get_db
            db = get_db()
            
            with db.session() as session:
                db_signal = Signal(
                    symbol=signal['symbol'],
                    timestamp=signal['timestamp'],
                    direction=signal['direction'],
                    confidence=signal['confidence'],
                    entry_price=signal['entry_price'],
                    sl_price=signal['sl_price'],
                    tp_price=signal['tp_price'],
                    technical_score=signal['technical_score'],
                    rsi=signal.get('rsi'),
                    macd_signal=signal.get('macd_signal'),
                    ma_signal=signal.get('ma_signal'),
                    patterns=signal.get('patterns'),
                    support_resistance=signal.get('support_resistance'),
                    trend_strength=signal.get('trend_strength'),
                    volatility=signal.get('volatility'),
                    volume_surge=signal.get('volume_surge'),
                    action_taken=signal.get('action', 'NONE'),
                    skip_reason=signal.get('skip_reason'),
                    strategy_name='SmartStrategyV2',
                    engine_version=self.VERSION,
                    full_analysis=signal.get('full_analysis')
                )
                session.add(db_signal)
                logger.debug(f"✅ Signal saved to DB: {signal['symbol']}")
        
        except Exception as e:
            logger.error(f"❌ Failed to save signal: {e}")
    
    def scan_and_analyze(self, top_n: int = 10) -> List[Dict]:
        """مسح السوق وتحليل أفضل العملات"""
        if not self.scanner:
            logger.warning("⚠️ Market Scanner not available")
            return []
        
        logger.info("🔍 Scanning market...")
        opportunities = self.scanner.scan_market(top_n=top_n)
        
        symbols = [opp['symbol'] for opp in opportunities]
        logger.info(f"✅ Found {len(symbols)} opportunities: {symbols}")
        
        signals = []
        for symbol in symbols:
            signal = self.analyze(symbol, save_to_db=True)
            if signal:
                signals.append(signal)
        
        # Filter ready signals
        ready_signals = [s for s in signals if s.get('action') == 'READY']
        logger.info(f"✅ {len(ready_signals)} signals ready for trading")
        
        return ready_signals


def main():
    """Test Signal Engine V3"""
    # Initialize
    try:
        client = Client() if Client else None
    except:
        client = None
    
    engine = SignalEngineV3(client=client)
    
    # Test single symbol
    symbol = 'BTCUSDT'
    signal = engine.analyze(symbol)
    
    if signal:
        print(f"\n{'='*80}")
        print(f"📡 SIGNAL: {signal['symbol']}")
        print(f"{'='*80}")
        print(f"Direction: {signal['direction']}")
        print(f"Confidence: {signal['confidence']}")
        print(f"Technical Score: {signal['technical_score']}/100")
        print(f"Entry: {signal['entry_price']}")
        print(f"SL: {signal['sl_price']}")
        print(f"TP: {signal['tp_price']}")
        print(f"Action: {signal.get('action', 'NONE')}")
        if signal.get('skip_reason'):
            print(f"Reason: {signal['skip_reason']}")
        print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
