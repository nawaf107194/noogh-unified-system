#!/usr/bin/env python3
"""
Smart Strategy V2 - الإستراتيجية الذكية v2 + Technical Analysis

التحسينات:
1. Market Scanner → أفضل 10 عملات (حجم, تقلب, زخم)
2. Technical Analyzer → أنماط, مؤشرات, دعم/مقاومة
3. فلاتر إدخال مشددة (Technical Score >= 70)
4. SL/TP محسّن (3% / 7.5% = 2.5:1 R:R)
5. حد أقصى 3 صفقات يومياً
"""

import sys
import time
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

try:
    from trading.market_scanner import MarketScanner
except ImportError:
    logger.warning("⚠️  Market Scanner not available")
    MarketScanner = None

try:
    from trading.technical_analyzer import TechnicalAnalyzer
except ImportError:
    logger.warning("⚠️  Technical Analyzer not available")
    TechnicalAnalyzer = None

try:
    from binance.client import Client
except ImportError:
    logger.warning("⚠️  Binance client not available")
    Client = None


class SmartStrategyV2:
    """الإستراتيجية الذكية v2"""
    
    def __init__(self, config: dict = None, binance_client = None):
        # Default optimized config
        self.config = config or {
            'stop_loss_pct': 3.0,
            'take_profit_pct': 7.5,
            'min_rrr': 2.5,
            'min_technical_score': 70,  # NEW: Technical score threshold
            'max_daily_trades': 3,
            'scanner_top_n': 10,
            'scanner_min_score': 70
        }
        
        # Initialize components
        self.scanner = MarketScanner() if MarketScanner else None
        self.technical = TechnicalAnalyzer() if TechnicalAnalyzer else None
        self.client = binance_client
        
        # Track state
        self.last_scan_time = 0
        self.current_symbols = []
        self.daily_trade_count = 0
        self.last_reset_date = datetime.now().date()
    
    def reset_daily_counter(self):
        """إعادة تعيين عداد الصفقات اليومي"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            self.daily_trade_count = 0
            self.last_reset_date = today
            logger.info("🗓️ Daily trade counter reset")
    
    def get_active_symbols(self) -> List[str]:
        """جلب العملات النشطة (يحدث كل ساعة)"""
        now = time.time()
        
        # Refresh every 1 hour
        if now - self.last_scan_time > 3600:
            if self.scanner:
                logger.info("🔍 Scanning market for best opportunities...")
                opportunities = self.scanner.scan_market(top_n=self.config['scanner_top_n'])
                
                # Filter by min score
                filtered = [
                    opp for opp in opportunities 
                    if opp['score'] >= self.config['scanner_min_score']
                ]
                
                self.current_symbols = [opp['symbol'] for opp in filtered]
                self.last_scan_time = now
                
                logger.info(f"✅ Active symbols: {self.current_symbols}")
            else:
                # Fallback to default
                self.current_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        
        return self.current_symbols
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """جلب بيانات OHLCV"""
        if not self.client:
            logger.warning(f"⚠️  No Binance client - skipping {symbol}")
            return None
        
        try:
            klines = self.client.futures_klines(symbol=symbol, interval=interval, limit=limit)
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert to float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"❌ Error fetching klines for {symbol}: {e}")
            return None
    
    def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """تحليل فني للعملة"""
        if not self.technical:
            logger.warning("⚠️  Technical Analyzer not available")
            return None
        
        # Get OHLCV data
        df = self.get_klines(symbol)
        if df is None or len(df) < 100:
            return None
        
        # Technical analysis
        analysis = self.technical.analyze(df, symbol=symbol)
        
        if 'error' in analysis:
            logger.warning(f"⚠️  {symbol}: {analysis['error']}")
            return None
        
        return analysis
    
    def validate_setup(self, symbol: str, analysis: Dict) -> tuple[bool, str]:
        """فحص الإعداد قبل الدخول"""
        # 1. Check daily limit
        if self.daily_trade_count >= self.config['max_daily_trades']:
            return False, f"Daily limit reached ({self.config['max_daily_trades']})"
        
        # 2. Check technical score
        tech_score = analysis.get('technical_score', 0)
        if tech_score < self.config['min_technical_score']:
            return False, f"Low technical score: {tech_score} < {self.config['min_technical_score']}"
        
        # 3. Check signal direction
        signal = analysis.get('signal', {})
        if signal.get('direction') == 'NEUTRAL':
            return False, "No clear direction"
        
        if not signal.get('should_enter', False):
            return False, "Signal says don't enter"
        
        # 4. Check confidence
        if signal.get('confidence') == 'LOW':
            return False, "Low confidence signal"
        
        return True, "All checks passed"
    
    def calculate_sl_tp(self, entry_price: float, side: str) -> dict:
        """حساب SL/TP المحسّن"""
        sl_pct = self.config['stop_loss_pct'] / 100
        tp_pct = self.config['take_profit_pct'] / 100
        
        if side == 'LONG':
            sl_price = entry_price * (1 - sl_pct)
            tp_price = entry_price * (1 + tp_pct)
        else:  # SHORT
            sl_price = entry_price * (1 + sl_pct)
            tp_price = entry_price * (1 - tp_pct)
        
        return {
            'sl_price': sl_price,
            'tp_price': tp_price,
            'sl_pct': self.config['stop_loss_pct'],
            'tp_pct': self.config['take_profit_pct'],
            'rrr': self.config['take_profit_pct'] / self.config['stop_loss_pct']
        }
    
    def should_enter_trade(self, symbol: str, analysis: Dict) -> bool:
        """قرار الدخول"""
        # Reset daily counter if needed
        self.reset_daily_counter()
        
        # Validate setup
        valid, reason = self.validate_setup(symbol, analysis)
        
        if not valid:
            logger.info(f"❌ {symbol}: {reason}")
            return False
        
        logger.info(f"✅ {symbol}: Setup validated - ENTER")
        return True
    
    def print_analysis_summary(self, symbol: str, analysis: Dict):
        """طباعة ملخص التحليل"""
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 {symbol} - Technical Analysis")
        logger.info(f"{'='*80}")
        
        logger.info(f"\n🎯 Technical Score: {analysis['technical_score']}/100")
        
        # Candlestick patterns
        patterns = analysis.get('candlestick_patterns', {})
        if patterns.get('patterns'):
            logger.info(f"\n🕯️  Patterns: {', '.join(patterns['patterns'])}")
            logger.info(f"   Bias: {patterns['bias']}")
        
        # Indicators
        indicators = analysis.get('indicators', {})
        logger.info(f"\n📊 Indicators:")
        logger.info(f"   RSI: {indicators.get('rsi', 0):.1f} ({indicators.get('rsi_signal', 'N/A')})")
        logger.info(f"   MACD: {indicators.get('macd_signal', 'N/A')}")
        logger.info(f"   MA: {indicators.get('ma_signal', 'N/A')}")
        
        # Support/Resistance
        sr = analysis.get('support_resistance', {})
        logger.info(f"\n📈 S/R:")
        logger.info(f"   Position: {sr.get('position', 'N/A')}")
        logger.info(f"   Nearest Support: {sr.get('nearest_support', 0):.2f} ({sr.get('support_distance_pct', 0):.1f}% away)")
        logger.info(f"   Nearest Resistance: {sr.get('nearest_resistance', 0):.2f} ({sr.get('resistance_distance_pct', 0):.1f}% away)")
        
        # Trend
        trend = analysis.get('trend', {})
        logger.info(f"\n📉 Trend:")
        logger.info(f"   Strength: {trend.get('trend_strength', 'N/A')} (ADX: {trend.get('adx', 0):.1f})")
        logger.info(f"   EMA Alignment: {trend.get('ema_alignment', 'N/A')}")
        
        # Signal
        signal = analysis.get('signal', {})
        logger.info(f"\n➡️  Signal:")
        logger.info(f"   Direction: {signal.get('direction', 'N/A')}")
        logger.info(f"   Confidence: {signal.get('confidence', 'N/A')}")
        logger.info(f"   Should Enter: {signal.get('should_enter', False)}")
        
        logger.info(f"\n{'='*80}\n")
    
    def execute_trade(self, symbol: str, analysis: Dict):
        """تنفيذ الصفقة"""
        signal = analysis['signal']
        side = signal['direction']
        
        # Get current price
        df = self.get_klines(symbol, limit=1)
        if df is None:
            logger.error(f"❌ Cannot get price for {symbol}")
            return None
        
        entry_price = df['close'].iloc[-1]
        sl_tp = self.calculate_sl_tp(entry_price, side)
        
        trade = {
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'sl_price': sl_tp['sl_price'],
            'tp_price': sl_tp['tp_price'],
            'rrr': sl_tp['rrr'],
            'technical_score': analysis['technical_score'],
            'confidence': signal['confidence'],
            'timestamp': datetime.now().isoformat()
        }
        
        self.daily_trade_count += 1
        
        logger.info(f"\n🟢 TRADE EXECUTED:")
        logger.info(f"   Symbol: {symbol}")
        logger.info(f"   Side: {side}")
        logger.info(f"   Entry: {entry_price}")
        logger.info(f"   SL: {sl_tp['sl_price']} (-{sl_tp['sl_pct']}%)")
        logger.info(f"   TP: {sl_tp['tp_price']} (+{sl_tp['tp_pct']}%)")
        logger.info(f"   R:R: {sl_tp['rrr']:.2f}:1")
        logger.info(f"   Technical Score: {analysis['technical_score']}/100")
        logger.info(f"   Confidence: {signal['confidence']}")
        logger.info(f"   Daily trades: {self.daily_trade_count}/{self.config['max_daily_trades']}\n")
        
        return trade
    
    def run_once(self):
        """دورة واحدة"""
        logger.info("\n" + "="*80)
        logger.info("🔄 Smart Strategy V2 - Cycle Start")
        logger.info("="*80 + "\n")
        
        # 1. Get active symbols from scanner
        symbols = self.get_active_symbols()
        
        # 2. For each symbol, analyze and decide
        for symbol in symbols:
            logger.info(f"🔍 Analyzing {symbol}...")
            
            # Technical analysis
            analysis = self.analyze_symbol(symbol)
            
            if analysis is None:
                logger.info(f"⚠️  {symbol}: Skipped (insufficient data)\n")
                continue
            
            # Print summary
            self.print_analysis_summary(symbol, analysis)
            
            # Decision
            if self.should_enter_trade(symbol, analysis):
                self.execute_trade(symbol, analysis)
            else:
                logger.info(f"❌ {symbol}: Not entering\n")
        
        logger.info("\n✅ Cycle complete\n")


def main():
    # Initialize Binance client (testnet or real)
    client = None
    if Client:
        try:
            client = Client()  # Add API keys if needed
        except:
            logger.warning("⚠️  Binance client initialization failed")
    
    strategy = SmartStrategyV2(binance_client=client)
    
    logger.info("🚀 Smart Strategy V2 + Technical Analysis initialized")
    logger.info(f"   Config: SL={strategy.config['stop_loss_pct']}%, TP={strategy.config['take_profit_pct']}%")
    logger.info(f"   Min Technical Score: {strategy.config['min_technical_score']}")
    logger.info(f"   Max Daily Trades: {strategy.config['max_daily_trades']}")
    logger.info(f"   Scanner: Top {strategy.config['scanner_top_n']} symbols\n")
    
    # Run once (or loop)
    strategy.run_once()


if __name__ == '__main__':
    main()
