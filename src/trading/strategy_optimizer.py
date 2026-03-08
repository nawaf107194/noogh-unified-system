#!/usr/bin/env python3
"""
Strategy Optimizer - محسّن الاستراتيجية
يحلل الصفقات السابقة ويقترح تحسينات للـ SL/TP وفلترة الإشارات

المشاكل المكتشفة:
1. Win Rate 32% (منخفض جداً)
2. SL يُضرب 80% من الوقت
3. Profit Factor 0.67 (خاسر)

الحلول:
1. توسيع SL لتقليل الـ noise
2. تشديد فلاتر الدخول
3. تحسين R:R ratio
"""

import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import json
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


class StrategyOptimizer:
    """محسّن الاستراتيجية"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / 'data' / 'shared_memory.sqlite')
        
        self.db_path = db_path
    
    def analyze_sl_tp_ratio(self) -> dict:
        """تحليل نسبة SL/TP الحالية"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get trades with entry/exit prices
            cursor.execute("""
                SELECT 
                    symbol, side, entry_price, pnl_pct, exit_reason, brain_confidence
                FROM paper_trades
                WHERE pnl_pct IS NOT NULL
            """)
            
            trades = cursor.fetchall()
            
            # Group by exit reason
            sl_hits = [t for t in trades if t[4] == 'STOP_LOSS']
            tp_hits = [t for t in trades if t[4] == 'TAKE_PROFIT']
            
            # Calculate average move before SL
            sl_avg_loss = sum(abs(float(t[3])) for t in sl_hits) / len(sl_hits) if sl_hits else 0
            tp_avg_win = sum(float(t[3]) for t in tp_hits) / len(tp_hits) if tp_hits else 0
            
            # Analyze by confidence
            high_conf = [t for t in trades if t[5] and float(t[5]) > 90]
            low_conf = [t for t in trades if t[5] and float(t[5]) < 70]
            
            high_conf_wr = sum(1 for t in high_conf if float(t[3]) > 0) / len(high_conf) * 100 if high_conf else 0
            low_conf_wr = sum(1 for t in low_conf if float(t[3]) > 0) / len(low_conf) * 100 if low_conf else 0
            
            return {
                'current_sl_avg': sl_avg_loss,
                'current_tp_avg': tp_avg_win,
                'sl_hit_rate': len(sl_hits) / len(trades) * 100,
                'tp_hit_rate': len(tp_hits) / len(trades) * 100,
                'high_conf_wr': high_conf_wr,
                'low_conf_wr': low_conf_wr,
                'high_conf_count': len(high_conf),
                'low_conf_count': len(low_conf)
            }
            
        finally:
            conn.close()
    
    def generate_recommendations(self, analysis: dict) -> dict:
        """توليد التوصيات"""
        recs = {
            'sl_adjustment': 'WIDEN',
            'tp_adjustment': 'KEEP',
            'confidence_filter': 85,
            'min_rrr': 2.5,
            'explanations': []
        }
        
        # 1. SL too tight (80% hit rate)
        if analysis['sl_hit_rate'] > 70:
            new_sl = analysis['current_sl_avg'] * 1.5  # Widen by 50%
            recs['recommended_sl'] = new_sl
            recs['explanations'].append(
                f"⚠️ SL hit rate is {analysis['sl_hit_rate']:.0f}% - WIDEN SL from {analysis['current_sl_avg']:.2f}% to {new_sl:.2f}%"
            )
        
        # 2. Low confidence trades perform poorly
        if analysis['low_conf_wr'] < analysis['high_conf_wr'] - 20:
            recs['explanations'].append(
                f"📊 High confidence trades: {analysis['high_conf_wr']:.0f}% WR vs Low confidence: {analysis['low_conf_wr']:.0f}% WR"
            )
            recs['explanations'].append(
                f"✅ FILTER OUT trades with confidence < {recs['confidence_filter']}"
            )
        
        # 3. R:R needs improvement
        current_rr = analysis['current_tp_avg'] / analysis['current_sl_avg'] if analysis['current_sl_avg'] > 0 else 0
        if current_rr < 2.0:
            recs['explanations'].append(
                f"⚖️ Current R:R = {current_rr:.2f} - INCREASE minimum R:R to {recs['min_rrr']}"
            )
        
        return recs
    
    def create_optimized_config(self, recs: dict) -> dict:
        """إنشاء ملف config محسّن"""
        config = {
            'strategy_version': '2.0_optimized',
            'risk_management': {
                'stop_loss_pct': recs.get('recommended_sl', 3.0),
                'take_profit_pct': 7.5,  # Maintain 2.5:1 R:R
                'min_rrr': recs['min_rrr'],
                'max_trades_per_day': 3,  # Reduce from unlimited
                'min_confidence': recs['confidence_filter']
            },
            'entry_filters': {
                'min_volume_surge': 1.8,  # Increase from 1.5
                'min_volatility': 3.5,     # Increase from 3.0
                'require_momentum_confirm': True,
                'avoid_chop_zones': True
            },
            'market_scanner': {
                'enabled': True,
                'top_n_symbols': 10,
                'refresh_interval': 3600,  # 1 hour
                'min_opportunity_score': 70
            },
            'updated_at': datetime.now().isoformat()
        }
        
        return config
    
    def save_config(self, config: dict):
        """حفظ الـ config"""
        config_path = Path(__file__).parent.parent / 'config' / 'trading_strategy_optimized.json'
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"✅ Saved optimized config to {config_path}")
    
    def print_report(self, analysis: dict, recs: dict):
        """طباعة التقرير"""
        print(f"\n{'='*90}")
        print("🔧 STRATEGY OPTIMIZATION REPORT")
        print(f"{'='*90}\n")
        
        print("📊 CURRENT PERFORMANCE:")
        print(f"  SL Hit Rate        : {analysis['sl_hit_rate']:.1f}% ❌")
        print(f"  TP Hit Rate        : {analysis['tp_hit_rate']:.1f}% ✅")
        print(f"  Avg SL Size        : {analysis['current_sl_avg']:.2f}%")
        print(f"  Avg TP Size        : {analysis['current_tp_avg']:.2f}%")
        print(f"  Current R:R        : {analysis['current_tp_avg']/analysis['current_sl_avg']:.2f}:1")
        print()
        
        print("🎯 CONFIDENCE ANALYSIS:")
        print(f"  High Confidence (>90) : {analysis['high_conf_wr']:.0f}% WR ({analysis['high_conf_count']} trades)")
        print(f"  Low Confidence (<70)  : {analysis['low_conf_wr']:.0f}% WR ({analysis['low_conf_count']} trades)")
        print()
        
        print(f"{'='*90}")
        print("💡 RECOMMENDATIONS:")
        print(f"{'='*90}\n")
        
        for i, exp in enumerate(recs['explanations'], 1):
            print(f"{i}. {exp}")
        
        print(f"\n{'='*90}")
        print("⚙️ OPTIMIZED SETTINGS:")
        print(f"{'='*90}\n")
        print(f"  Stop Loss          : {recs.get('recommended_sl', 3.0):.2f}%")
        print(f"  Take Profit        : 7.50%")
        print(f"  Min R:R            : {recs['min_rrr']}:1")
        print(f"  Min Confidence     : {recs['confidence_filter']}")
        print(f"  Max Daily Trades   : 3")
        print()
        
        print(f"{'='*90}\n")
    
    def run(self):
        logger.info("\n🔧 Starting Strategy Optimization...\n")
        
        # 1. Analyze current performance
        analysis = self.analyze_sl_tp_ratio()
        
        # 2. Generate recommendations
        recs = self.generate_recommendations(analysis)
        
        # 3. Create optimized config
        config = self.create_optimized_config(recs)
        
        # 4. Print report
        self.print_report(analysis, recs)
        
        # 5. Save config
        self.save_config(config)
        
        logger.info("✅ Optimization complete!\n")
        logger.info("📝 Next steps:")
        logger.info("   1. Review optimized config: config/trading_strategy_optimized.json")
        logger.info("   2. Update advanced_strategy.py to use new settings")
        logger.info("   3. Run paper trading with new config for 50+ trades")
        logger.info("   4. Re-analyze and iterate\n")


if __name__ == '__main__':
    optimizer = StrategyOptimizer()
    optimizer.run()
