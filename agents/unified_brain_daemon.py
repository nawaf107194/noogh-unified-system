# Unified Brain Daemon - الدماغ الموحد
# المركز العصبي للنظام - يربط كل المكونات

import asyncio
import logging
import json
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Core components
from agents.unified_context import UnifiedContext
from agents.proactive_research_agent import ProactiveResearchAgent
from agents.brain_research_orchestrator import BrainResearchOrchestrator

logger = logging.getLogger(__name__)


class UnifiedBrainDaemon:
    """
    الدماغ الموحد - المنسق الرئيسي للنظام.
    
    يقوم بـ:
    1. مراقبة حالة النظام (عبر UnifiedContext)
    2. بحث استباقي (عبر ProactiveResearchAgent)
    3. تنسيق الوكلاء (عبر BrainOrchestrator)
    4. تدريب مستمر (integration مع ContinuousTrainingLoop)
    5. تحديث الاستراتيجيات (neurons → trading)
    
    الحلقة الكاملة:
    Trading → Context → Research → Neurons → Training → Strategy → Trading
    """

    def __init__(self):
        # Core components
        self.context = UnifiedContext()
        self.proactive_agent = ProactiveResearchAgent(context=self.context)
        self.orchestrator = BrainResearchOrchestrator()
        
        # State
        self.running = False
        self.cycle_count = 0
        self.start_time = None
        
        # Config
        self.think_cycle_interval = 60 * 15  # 15 دقيقة
        self.deep_analysis_interval = 60 * 60  # ساعة واحدة
        
        logger.info("🧠 UnifiedBrainDaemon initialized")

    async def think_cycle(self):
        """
        دورة تفكير كاملة (كل 15 دقيقة).
        
        Workflow:
        1. تحديث السياق من التداول
        2. تقييم الحاجة للبحث
        3. تنفيذ بحث إذا لزم
        4. مراجعة neurons النشطة
        5. تقييم الأداء
        """
        self.cycle_count += 1
        cycle_start = datetime.now()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🧠 THINK CYCLE #{self.cycle_count} - {cycle_start.strftime('%H:%M:%S')}")
        logger.info(f"{'='*70}")
        
        try:
            # Step 1: تحديث السياق
            logger.info("📊 Step 1: Updating context from trading...")
            self.context.update_from_trading()
            
            # طباعة ملخص
            summary = self.context.get_summary()
            logger.info(f"   Regime: {summary['state']['market_regime']}")
            logger.info(f"   Recent PnL: {summary['state']['recent_pnl']:.2f}%")
            logger.info(f"   Win Rate (7d): {summary['state']['win_rate_7d']:.1%}")
            logger.info(f"   Active Neurons: {summary['state']['active_neurons_count']}")
            
            if summary['knowledge_gaps']:
                logger.info(f"   Knowledge Gaps: {len(summary['knowledge_gaps'])}")
                for gap in summary['knowledge_gaps'][:3]:
                    logger.info(f"      - {gap}")
            
            # Step 2: فحص الحاجة للبحث
            logger.info("\n🔍 Step 2: Checking if research needed...")
            topic = self.proactive_agent.should_trigger_research()
            
            if topic:
                # Step 3: تنفيذ بحث
                logger.info(f"\n🎯 Step 3: Research triggered - '{topic}'")
                research_result = await self.proactive_agent.execute_research(topic)
                
                if research_result:
                    logger.info(f"   ✅ Neurons generated: {research_result.get('neurons_generated', 0)}")
                    logger.info(f"   ✅ Sources used: {len(research_result.get('research', {}).get('sources', {}))}")
            else:
                logger.info("   ✅ No research needed - system performing well")
            
            # Step 4: مراجعة neurons النشطة
            logger.info("\n🧠 Step 4: Reviewing active neurons...")
            active_neurons = self.context.get_active_neurons()
            logger.info(f"   Active research neurons: {len(active_neurons)}")
            
            if active_neurons:
                for i, neuron in enumerate(active_neurons[:3], 1):
                    logger.info(f"   {i}. {neuron.get('concept', '')[:60]}...")
            
            # Step 5: تقييم الأداء
            logger.info("\n📊 Step 5: Performance evaluation")
            performance = self._evaluate_performance()
            logger.info(f"   Overall Score: {performance['overall_score']:.1%}")
            logger.info(f"   Learning Effectiveness: {performance['learning_effectiveness']:.1%}")
            logger.info(f"   Research Impact: {performance['research_impact']:.1%}")
            
            # ختام
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            logger.info(f"\n✅ Cycle #{self.cycle_count} complete in {cycle_duration:.1f}s")
            logger.info(f"{'='*70}\n")
            
        except Exception as e:
            logger.error(f"❌ Error in think cycle: {e}", exc_info=True)

    async def deep_analysis_cycle(self):
        """
        تحليل عميق (كل ساعة).
        
        - مراجعة شاملة للأخطاء
        - تحليل الأنماط
        - تخطيط استراتيجيات التحسين
        """
        logger.info("\n" + "#"*70)
        logger.info("🔬 DEEP ANALYSIS CYCLE")
        logger.info("#"*70)
        
        try:
            # تحليل الأخطاء المتكررة
            mistake_patterns = self._analyze_mistakes()
            
            if mistake_patterns:
                logger.info("\n🚨 Recurring Mistake Patterns:")
                for pattern, count in mistake_patterns.items():
                    logger.info(f"   {pattern}: {count} occurrences")
                    
                    # بحث تلقائي عن حلول
                    topic = f"solve {pattern} in trading"
                    logger.info(f"   🔍 Researching solution: '{topic}'")
                    await self.orchestrator.research_and_generate(topic, sources=['arxiv', 'github'])
            
            # تقييم فعالية البحث
            research_effectiveness = self._evaluate_research_effectiveness()
            logger.info(f"\n📊 Research Effectiveness: {research_effectiveness:.1%}")
            
            # اقتراحات للتحسين
            suggestions = self._generate_improvement_suggestions()
            if suggestions:
                logger.info("\n💡 Improvement Suggestions:")
                for suggestion in suggestions:
                    logger.info(f"   - {suggestion}")
            
            logger.info("\n" + "#"*70 + "\n")
            
        except Exception as e:
            logger.error(f"❌ Error in deep analysis: {e}", exc_info=True)

    def _evaluate_performance(self) -> Dict:
        """تقييم الأداء العام"""
        # حساب مبسط
        win_rate = self.context.state.win_rate_7d
        pnl_positive = 1.0 if self.context.state.recent_pnl > 0 else 0.5
        
        # فعالية التعلم
        learning_effectiveness = min(self.context.state.active_neurons_count / 50, 1.0)
        
        # تأثير البحث
        research_stats = self.proactive_agent.get_stats()
        research_impact = research_stats.get('success_rate', 0.5)
        
        # Overall
        overall = (win_rate * 0.5 + pnl_positive * 0.3 + learning_effectiveness * 0.1 + research_impact * 0.1)
        
        return {
            'overall_score': overall,
            'win_rate': win_rate,
            'pnl_status': pnl_positive,
            'learning_effectiveness': learning_effectiveness,
            'research_impact': research_impact
        }

    def _analyze_mistakes(self) -> Dict[str, int]:
        """تحليل الأخطاء المتكررة"""
        # أخذ من losing_patterns
        patterns = {}
        for pattern in self.context.losing_patterns:
            patterns[pattern] = patterns.get(pattern, 0) + 1
        return patterns

    def _evaluate_research_effectiveness(self) -> float:
        """تقييم فعالية البحث"""
        stats = self.proactive_agent.get_stats()
        return stats.get('success_rate', 0.5)

    def _generate_improvement_suggestions(self) -> List[str]:
        """اقتراحات للتحسين"""
        suggestions = []
        
        if self.context.state.win_rate_7d < 0.6:
            suggestions.append("Focus on quality over quantity - reduce trade frequency")
        
        if self.context.state.recent_pnl < -3:
            suggestions.append("Implement stricter risk management - reduce position sizes")
        
        if len(self.context.losing_patterns) > 2:
            suggestions.append(f"Add filters to avoid: {', '.join(self.context.losing_patterns[:2])}")
        
        return suggestions

    async def run_daemon(self):
        """
        تشغيل الدماغ كـ daemon مستمر.
        """
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("\n" + "="*70)
        logger.info("🧠 UNIFIED BRAIN DAEMON STARTED")
        logger.info(f"   Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"   Think Cycle: Every {self.think_cycle_interval // 60} minutes")
        logger.info(f"   Deep Analysis: Every {self.deep_analysis_interval // 60} minutes")
        logger.info("="*70 + "\n")
        
        last_deep_analysis = datetime.now()
        
        try:
            while self.running:
                # Think cycle
                await self.think_cycle()
                
                # Deep analysis (إذا مر ساعة)
                if (datetime.now() - last_deep_analysis).total_seconds() >= self.deep_analysis_interval:
                    await self.deep_analysis_cycle()
                    last_deep_analysis = datetime.now()
                
                # انتظار
                await asyncio.sleep(self.think_cycle_interval)
                
        except asyncio.CancelledError:
            logger.info("🛑 Daemon stopped gracefully")
        except Exception as e:
            logger.error(f"❌ Fatal error in daemon: {e}", exc_info=True)
        finally:
            self.running = False
            uptime = datetime.now() - self.start_time
            logger.info(f"\n📊 Final Stats:")
            logger.info(f"   Uptime: {uptime}")
            logger.info(f"   Total Cycles: {self.cycle_count}")

    def stop(self):
        """إيقاف الدماغ"""
        logger.info("🛑 Stopping brain daemon...")
        self.running = False


async def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/home/noogh/projects/noogh_unified_system/src/logs/unified_brain.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create daemon
    brain = UnifiedBrainDaemon()
    
    # Handle signals
    def signal_handler(sig, frame):
        logger.info(f"\n🚨 Received signal {sig}")
        brain.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run
    await brain.run_daemon()


if __name__ == '__main__':
    asyncio.run(main())