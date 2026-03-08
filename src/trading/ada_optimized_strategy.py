#!/usr/bin/env python3
"""
ADA-Optimized Strategy

مبني على تحليل البيانات:
- ADAUSDT: 66.7% win rate
- Best Trade: +22.87%
- Direction: SHORT (3 صفقات، كلها ناجحة تقريباً)
- Total PnL: +24.37%

الاستراتيجية:
1. تركيز على ADAUSDT فقط
2. SHORT positions فقط (أداء أفضل)
3. دخول عند مقاومة
4. SL = ATR × 2
5. TP = Entry - (2.5 × SL)
6. Trailing Stop نشط
7. Timeout: 12 ساعات
"""

import sys
from pathlib import Path
import logging
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading.advanced_strategy import AdvancedFuturesStrategy

logger = logging.getLogger(__name__)

class ADAOptimizedStrategy(AdvancedFuturesStrategy):
    """
    استراتيجية محسّنة لـ ADAUSDT
    مبنية على أفضل أداء تاريخي (66.7% win rate)
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ADA-specific settings
        self.SYMBOL = 'ADAUSDT'
        self.DIRECTION = 'SHORT'  # أداء تاريخي أفضل
        self.MIN_WIN_RATE = 0.60  # هدف: حافظ على 60%+
        self.MAX_HOLDING_TIME = 12 * 3600  # 12 hours
        
        # Risk settings (محافظ)
        self.RISK_PER_TRADE = 0.008  # 0.8% (أقل من 1%)
        self.MIN_RRR = 2.5  # Risk-Reward: 1:2.5
        
        # Entry rules
        self.RESISTANCE_LOOKBACK = 20  # آخر 20 شمعة
        self.ATR_MULTIPLIER_SL = 2.0
        self.ATR_MULTIPLIER_TP = 2.5
        
        # Trailing stop
        self.TRAILING_STOP_ACTIVATION = 0.015  # عند +1.5%
        self.TRAILING_STOP_DISTANCE = 0.008   # 0.8% من الذروة
        
        logger.info("🎯 ADA-Optimized Strategy initialized")
        logger.info(f"   Direction: {self.DIRECTION}")
        logger.info(f"   Min Win Rate: {self.MIN_WIN_RATE:.1%}")
        logger.info(f"   Max Holding: {self.MAX_HOLDING_TIME/3600:.0f}h")
    
    def should_trade_ada(self) -> bool:
        """
        فحص إذا يجب التداول على ADA الآن
        """
        # 1. تحقق من Win Rate الأخير
        recent_trades = self.get_recent_trades(symbol='ADAUSDT', days=7)
        
        if len(recent_trades) >= 5:
            wins = sum(1 for t in recent_trades if t['pnl'] > 0)
            win_rate = wins / len(recent_trades)
            
            if win_rate < self.MIN_WIN_RATE:
                logger.warning(f"⚠️ ADA Win Rate low: {win_rate:.1%}")
                return False
        
        # 2. تحقق من السوق
        if not self._check_market_conditions():
            return False
        
        # 3. تحقق من news filter
        if self._is_news_time():
            logger.info("📰 News window - skip trade")
            return False
        
        return True
    
    def analyze_ada_setup(self):
        """
        تحليل setup لـ ADAUSDT
        """
        if not self.should_trade_ada():
            return None
        
        # استخدم analyze_setup من AdvancedStrategy
        setup = self.analyze_setup(symbol=self.SYMBOL)
        
        if not setup or not setup.get('entry_price'):
            return None
        
        # فلتر إضافي: فقط SHORT
        if setup['direction'] != 'SHORT':
            logger.info(f"🔴 Skipping LONG signal (SHORT-only strategy)")
            return None
        
        # فلتر RRR
        rrr = setup.get('rrr', 0)
        if rrr < self.MIN_RRR:
            logger.info(f"⚠️ RRR too low: {rrr:.2f} < {self.MIN_RRR}")
            return None
        
        # حساب position size
        setup['position_size'] = self._calculate_position_size(
            entry=setup['entry_price'],
            stop_loss=setup['stop_loss']
        )
        
        # إضافة timeout
        setup['timeout'] = datetime.now() + timedelta(seconds=self.MAX_HOLDING_TIME)
        
        logger.info(f"✅ ADA Setup Ready:")
        logger.info(f"   Entry: {setup['entry_price']}")
        logger.info(f"   SL: {setup['stop_loss']} (-{abs((setup['stop_loss']-setup['entry_price'])/setup['entry_price'])*100:.2f}%)")
        logger.info(f"   TP: {setup['take_profit']} (+{abs((setup['take_profit']-setup['entry_price'])/setup['entry_price'])*100:.2f}%)")
        logger.info(f"   RRR: 1:{rrr:.2f}")
        logger.info(f"   Size: {setup['position_size']:.4f} ADA")
        
        return setup
    
    def _calculate_position_size(self, entry: float, stop_loss: float) -> float:
        """
        حساب حجم الصفقة بناءً على المخاطرة
        """
        # المخاطرة = 0.8% من رأس المال
        account_balance = self.get_account_balance()  # من AdvancedStrategy
        risk_amount = account_balance * self.RISK_PER_TRADE
        
        # حساب المسافة للـ SL
        sl_distance = abs(entry - stop_loss)
        
        # Position size
        position_size = risk_amount / sl_distance
        
        return position_size
    
    def monitor_ada_trade(self, trade_id: str):
        """
        مراقبة صفقة ADA النشطة
        """
        trade = self.get_trade_by_id(trade_id)
        
        if not trade:
            return
        
        current_price = self.get_current_price(self.SYMBOL)
        entry_price = trade['entry_price']
        
        # حساب PnL
        if trade['direction'] == 'SHORT':
            pnl_pct = (entry_price - current_price) / entry_price
        else:
            pnl_pct = (current_price - entry_price) / entry_price
        
        logger.info(f"📊 ADA Trade Monitor: PnL {pnl_pct*100:+.2f}%")
        
        # 1. تحقق من Trailing Stop
        if pnl_pct >= self.TRAILING_STOP_ACTIVATION:
            self._activate_trailing_stop(trade, current_price, pnl_pct)
        
        # 2. تحقق من Timeout
        if datetime.now() >= trade.get('timeout', datetime.max):
            logger.info("⏰ Timeout reached - closing trade")
            self.close_trade(trade_id, reason='timeout')
            return
        
        # 3. تحقق من TP/SL
        if trade['direction'] == 'SHORT':
            if current_price <= trade['take_profit']:
                logger.info("🎯 TP Hit!")
                self.close_trade(trade_id, reason='take_profit')
            elif current_price >= trade['stop_loss']:
                logger.info("🛑 SL Hit")
                self.close_trade(trade_id, reason='stop_loss')
        else:
            if current_price >= trade['take_profit']:
                logger.info("🎯 TP Hit!")
                self.close_trade(trade_id, reason='take_profit')
            elif current_price <= trade['stop_loss']:
                logger.info("🛑 SL Hit")
                self.close_trade(trade_id, reason='stop_loss')
    
    def _activate_trailing_stop(self, trade, current_price, pnl_pct):
        """
        تفعيل Trailing Stop
        """
        if trade.get('trailing_active'):
            # تحديث trailing stop
            if trade['direction'] == 'SHORT':
                # للـ SHORT: trailing stop يتحرك للأسفل
                new_stop = current_price * (1 + self.TRAILING_STOP_DISTANCE)
                if new_stop < trade['trailing_stop']:
                    trade['trailing_stop'] = new_stop
                    logger.info(f"📉 Trailing Stop updated: {new_stop:.6f}")
            else:
                # للـ LONG: trailing stop يتحرك للأعلى
                new_stop = current_price * (1 - self.TRAILING_STOP_DISTANCE)
                if new_stop > trade['trailing_stop']:
                    trade['trailing_stop'] = new_stop
                    logger.info(f"📈 Trailing Stop updated: {new_stop:.6f}")
        else:
            # تفعيل لأول مرة
            if trade['direction'] == 'SHORT':
                trade['trailing_stop'] = current_price * (1 + self.TRAILING_STOP_DISTANCE)
            else:
                trade['trailing_stop'] = current_price * (1 - self.TRAILING_STOP_DISTANCE)
            
            trade['trailing_active'] = True
            logger.info(f"✅ Trailing Stop activated at {pnl_pct*100:.2f}%")
            logger.info(f"   Initial stop: {trade['trailing_stop']:.6f}")
    
    def _check_market_conditions(self) -> bool:
        """
        فحص شروط السوق
        """
        # TODO: إضافة فحوصات إضافية
        # - Volatility check
        # - Volume check
        # - Trend confirmation
        
        return True
    
    def _is_news_time(self) -> bool:
        """
        فحص إذا كان وقت أخبار
        """
        # TODO: تكامل مع economic calendar
        return False
    
    def get_recent_trades(self, symbol: str, days: int = 7):
        """
        جلب الصفقات الأخيرة
        """
        # TODO: تكامل مع database
        return []
    
    def get_account_balance(self) -> float:
        """
        جلب رصيد الحساب
        """
        # TODO: تكامل مع Binance API
        return 1000.0  # placeholder
    
    def get_current_price(self, symbol: str) -> float:
        """
        جلب السعر الحالي
        """
        # TODO: تكامل مع Binance API
        return 0.0
    
    def get_trade_by_id(self, trade_id: str):
        """
        جلب صفقة بالـ ID
        """
        # TODO: تكامل مع database
        return None
    
    def close_trade(self, trade_id: str, reason: str):
        """
        إغلاق صفقة
        """
        logger.info(f"🔴 Closing trade {trade_id}: {reason}")
        # TODO: تكامل مع Binance API


if __name__ == '__main__':
    # Test
    strategy = ADAOptimizedStrategy()
    
    # تحليل setup
    setup = strategy.analyze_ada_setup()
    
    if setup:
        print("\n✅ Setup Ready!")
        print(f"Symbol: {strategy.SYMBOL}")
        print(f"Direction: {setup['direction']}")
        print(f"Entry: {setup['entry_price']}")
        print(f"SL: {setup['stop_loss']}")
        print(f"TP: {setup['take_profit']}")
        print(f"RRR: 1:{setup['rrr']:.2f}")
    else:
        print("\n⚠️ No setup found")
