#!/usr/bin/env python3
"""
Smart Strategy V2 - الإستراتيجية الذكية v2

التحسينات:
1. يستخدم Market Scanner لاختيار أفضل 10 عملات
2. فلاتر إدخال مشددة (min confidence 85)
3. SL/TP محسّن (3% / 7.5% = 2.5:1 R:R)
4. حد أقصى 3 صفقات يومياً
5. تعلّم من Neuron Fabric
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

try:
    from trading.market_scanner import MarketScanner
except ImportError:
    logger.warning("Market Scanner not available")
    MarketScanner = None


class SmartStrategyV2:
    """الإستراتيجية الذكية v2"""
    
    def __init__(self, config: dict = None):
        # Default optimized config
        self.config = config or {
            'stop_loss_pct': 3.0,
            'take_profit_pct': 7.5,
            'min_rrr': 2.5,
            'min_confidence': 85,
            'max_daily_trades': 3,
            'min_volume_surge': 1.8,
            'min_volatility': 3.5,
            'scanner_top_n': 10,
            'scanner_min_score': 70
        }
        
        # Initialize scanner
        self.scanner = MarketScanner() if MarketScanner else None
        
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
    
    def validate_setup(self, setup: dict) -> tuple[bool, str]:
        """فحص الإعداد قبل الدخول"""
        # 1. Check daily limit
        if self.daily_trade_count >= self.config['max_daily_trades']:
            return False, f"Daily limit reached ({self.config['max_daily_trades']})"
        
        # 2. Check confidence
        if setup.get('confidence', 0) < self.config['min_confidence']:
            return False, f"Low confidence: {setup.get('confidence')} < {self.config['min_confidence']}"
        
        # 3. Check R:R
        rrr = setup.get('rrr', 0)
        if rrr < self.config['min_rrr']:
            return False, f"Low R:R: {rrr:.2f} < {self.config['min_rrr']}"
        
        # 4. Check volatility (from setup or scanner)
        volatility = setup.get('volatility', 0)
        if volatility > 0 and volatility < self.config['min_volatility']:
            return False, f"Low volatility: {volatility:.1f}% < {self.config['min_volatility']}%"
        
        # 5. Check volume
        volume_surge = setup.get('volume_surge', 1.0)
        if volume_surge < self.config['min_volume_surge']:
            return False, f"Low volume surge: {volume_surge:.1f}x < {self.config['min_volume_surge']}x"
        
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
    
    def should_enter_trade(self, symbol: str, setup: dict) -> bool:
        """قرار الدخول"""
        # Reset daily counter if needed
        self.reset_daily_counter()
        
        # Validate setup
        valid, reason = self.validate_setup(setup)
        
        if not valid:
            logger.info(f"❌ {symbol}: {reason}")
            return False
        
        # Check historical performance (optional - from Neuron Fabric)
        # historical_wr = self.check_historical_performance(symbol, setup)
        # if historical_wr and historical_wr < 0.3:
        #     logger.warning(f"⚠️ {symbol}: Historical WR too low ({historical_wr:.0%})")
        #     return False
        
        logger.info(f"✅ {symbol}: Setup validated - ENTER")
        return True
    
    def execute_trade(self, symbol: str, side: str, entry_price: float, setup: dict):
        """تنفيذ الصفقة"""
        sl_tp = self.calculate_sl_tp(entry_price, side)
        
        trade = {
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'sl_price': sl_tp['sl_price'],
            'tp_price': sl_tp['tp_price'],
            'rrr': sl_tp['rrr'],
            'confidence': setup.get('confidence'),
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
        logger.info(f"   Daily trades: {self.daily_trade_count}/{self.config['max_daily_trades']}\n")
        
        return trade
    
    def run_once(self):
        """دورة واحدة"""
        logger.info("\n" + "="*80)
        logger.info("🔄 Smart Strategy V2 - Cycle Start")
        logger.info("="*80 + "\n")
        
        # 1. Get active symbols from scanner
        symbols = self.get_active_symbols()
        
        # 2. For each symbol, check for setup
        for symbol in symbols:
            # Here you would integrate with your actual signal engine
            # For now, this is a placeholder
            logger.info(f"🔍 Checking {symbol}...")
            
            # Example: Get setup from SignalEngineV3
            # setup = signal_engine.analyze(symbol)
            # if setup and self.should_enter_trade(symbol, setup):
            #     self.execute_trade(symbol, setup['side'], setup['price'], setup)
        
        logger.info("\n✅ Cycle complete\n")


def main():
    strategy = SmartStrategyV2()
    
    logger.info("🚀 Smart Strategy V2 initialized")
    logger.info(f"   Config: SL={strategy.config['stop_loss_pct']}%, TP={strategy.config['take_profit_pct']}%")
    logger.info(f"   Min Confidence: {strategy.config['min_confidence']}")
    logger.info(f"   Max Daily Trades: {strategy.config['max_daily_trades']}")
    logger.info(f"   Scanner: Top {strategy.config['scanner_top_n']} symbols\n")
    
    # Run once (or loop)
    strategy.run_once()


if __name__ == '__main__':
    main()
