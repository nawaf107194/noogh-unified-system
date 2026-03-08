# Proactive Research Agent - وكيل بحث استباقي
# يقرر متى وماذا يبحث بدون تدخل بشري

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path

from agents.unified_context import UnifiedContext
from agents.brain_research_orchestrator import brain_think_and_research

logger = logging.getLogger(__name__)


class ProactiveResearchAgent:
    """
    وكيل بحث استباقي - يراقب ويتخذ قرار البحث تلقائياً.
    
    Triggers:
    1. خسائر متتالية ≥ 3
    2. Market regime تغير
    3. Neurons performance تراجع
    4. فجوة معرفية مكتشفة
    5. Win rate < 50%
    """

    def __init__(self, context: UnifiedContext = None):
        self.context = context or UnifiedContext()
        self.last_research_time = None
        self.min_research_interval = timedelta(hours=2)  # أقل مسافة بين بحثين
        self.research_history: List[Dict] = []
        
        logger.info("🔍 ProactiveResearchAgent initialized")

    def consecutive_losses(self) -> int:
        """حساب عدد الخسائر المتتالية"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.context.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT json_extract(value, '$.pnl')
                FROM beliefs 
                WHERE key LIKE 'trade:%'
                ORDER BY updated_at DESC
                LIMIT 10
            """)
            
            recent_trades = [float(row[0]) for row in cursor.fetchall() if row[0]]
            conn.close()
            
            # عد الخسائر المتتالية من البداية
            losses = 0
            for pnl in recent_trades:
                if pnl < 0:
                    losses += 1
                else:
                    break
            
            return losses
            
        except Exception as e:
            logger.error(f"Error calculating losses: {e}")
            return 0

    def regime_changed_recently(self) -> bool:
        """هل تغير الـ regime مؤخراً؟"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.context.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT json_extract(value, '$.regime')
                FROM beliefs 
                WHERE key = 'market:current_regime'
                AND updated_at > datetime('now', '-1 hour')
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] != self.context.state.market_regime:
                return True
            
        except:
            pass
        
        return False

    def neurons_performance_low(self) -> bool:
        """هل أداء الـ neurons منخفض؟"""
        # بسيط: إذا win rate < 60%
        return self.context.state.win_rate_7d < 0.6

    def should_trigger_research(self) -> Optional[str]:
        """
        قرار: هل نبحث الآن؟
        
        Returns:
            موضوع البحث أو None
        """
        # فحص: هل مر وقت كاف منذ آخر بحث؟
        if self.last_research_time:
            elapsed = datetime.now() - self.last_research_time
            if elapsed < self.min_research_interval:
                return None
        
        # Trigger 1: خسائر متتالية
        losses = self.consecutive_losses()
        if losses >= 3:
            logger.warning(f"🚨 Trigger: {losses} consecutive losses")
            return "risk management strategies crypto trading"
        
        # Trigger 2: Regime تغير
        if self.regime_changed_recently():
            new_regime = self.context.state.market_regime
            logger.info(f"🔄 Trigger: Market regime changed to {new_regime}")
            return f"trading strategies for {new_regime} market conditions"
        
        # Trigger 3: Neurons performance منخفض
        if self.neurons_performance_low():
            logger.info("📉 Trigger: Neurons performance below threshold")
            return "neural network optimization techniques trading"
        
        # Trigger 4: فجوة معرفية من Context
        if self.context.knowledge_gaps:
            gap = self.context.knowledge_gaps[0]  # أعلى أولوية
            logger.info(f"📖 Trigger: Knowledge gap detected - {gap}")
            return gap
        
        # Trigger 5: Win rate منخفض جداً
        if self.context.state.win_rate_7d < 0.5:
            logger.warning(f"⚠️ Trigger: Win rate critically low ({self.context.state.win_rate_7d:.1%})")
            return "improve win rate trading strategies"
        
        return None

    async def execute_research(self, topic: str) -> Dict:
        """تنفيذ بحث وتسجيل النتيجة"""
        logger.info(f"🎯 Proactive research triggered: '{topic}'")
        
        try:
            # تنفيذ البحث
            result = await brain_think_and_research(
                topic=topic,
                sources=['youtube', 'github', 'arxiv'],
                generate_neurons=True
            )
            
            # تسجيل
            self.last_research_time = datetime.now()
            self.research_history.append({
                'topic': topic,
                'timestamp': self.last_research_time.isoformat(),
                'neurons_generated': result.get('neurons_generated', 0),
                'success': True
            })
            
            logger.info(f"✅ Research completed: {result.get('neurons_generated', 0)} neurons generated")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Research failed: {e}")
            self.research_history.append({
                'topic': topic,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
            return {}

    async def run_continuous(self, check_interval_minutes: int = 30):
        """
        حلقة مستمرة - يراقب ويبحث تلقائياً.
        
        Args:
            check_interval_minutes: مدة الفحص (دقائق)
        """
        logger.info(f"🔄 ProactiveResearchAgent started (check every {check_interval_minutes}min)")
        
        while True:
            try:
                # 1) تحديث السياق
                self.context.update_from_trading()
                
                # 2) فحص: هل نحتاج بحث؟
                topic = self.should_trigger_research()
                
                if topic:
                    # 3) تنفيذ البحث
                    await self.execute_research(topic)
                else:
                    logger.debug("✅ No research needed at this time")
                
                # 4) انتظار
                await asyncio.sleep(check_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"❌ Error in proactive loop: {e}")
                await asyncio.sleep(300)  # 5 دقائق عند الخطأ

    def get_stats(self) -> Dict:
        """إحصائيات البحث الاستباقي"""
        total = len(self.research_history)
        successful = len([r for r in self.research_history if r.get('success')])
        
        return {
            'total_researches': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': successful / total if total > 0 else 0,
            'last_research': self.last_research_time.isoformat() if self.last_research_time else None,
            'recent_history': self.research_history[-5:]  # آخر 5
        }


if __name__ == '__main__':
    import sys
    
    async def main():
        agent = ProactiveResearchAgent()
        
        if '--once' in sys.argv:
            # فحص مرة واحدة
            agent.context.update_from_trading()
            topic = agent.should_trigger_research()
            
            if topic:
                print(f"🔍 Research triggered: {topic}")
                result = await agent.execute_research(topic)
                print(f"\n✅ Result: {result.get('neurons_generated', 0)} neurons")
            else:
                print("✅ No research needed")
        else:
            # حلقة مستمرة
            await agent.run_continuous(check_interval_minutes=30)
    
    asyncio.run(main())