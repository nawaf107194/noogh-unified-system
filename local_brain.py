#!/usr/bin/env python3
# Local Brain - الدماغ المحلي الجاهز للتشغيل
# نقطة دخول سهلة لتشغيل كل شيء: التعلم + البحث + التدريب + التداول

"""
Local Brain - الدماغ المحلي المتكامل

الاستخدامات:

1. تشغيل الدماغ كاملاً (وضع daemon):
   python3 local_brain.py --daemon

2. دورة تفكير واحدة:
   python3 local_brain.py --once

3. بحث عن موضوع محدد:
   python3 local_brain.py --research "transformer efficiency"

4. تحليل الوضع الحالي:
   python3 local_brain.py --status

5. إحصائيات النظام:
   python3 local_brain.py --stats
"""

import asyncio
import argparse
import logging
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.unified_context import UnifiedContext
from agents.unified_brain_daemon import UnifiedBrainDaemon
from agents.brain_research_orchestrator import brain_think_and_research

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalBrain:
    """
    واجهة مبسطة للدماغ المحلي.
    """

    def __init__(self):
        self.context = UnifiedContext()
        self.daemon = UnifiedBrainDaemon()

    async def run_daemon(self):
        """تشغيل الدماغ كـ daemon مستمر"""
        logger.info("🧠 Starting Local Brain Daemon...")
        logger.info("   Press Ctrl+C to stop\n")
        
        try:
            await self.daemon.run_daemon()
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping daemon...")

    async def run_once(self):
        """دورة تفكير واحدة فقط"""
        logger.info("🧠 Running single think cycle...\n")
        await self.daemon.think_cycle()
        logger.info("\n✅ Single cycle complete")

    async def research_topic(self, topic: str):
        """بحث عن موضوع محدد"""
        logger.info(f"🔍 Researching: '{topic}'\n")
        
        result = await brain_think_and_research(
            topic=topic,
            sources=['youtube', 'github', 'arxiv'],
            generate_neurons=True
        )
        
        logger.info("\n✅ Research complete!")
        logger.info(f"   Neurons generated: {result.get('neurons_generated', 0)}")
        logger.info(f"   Sources used: {len(result.get('research', {}).get('sources', {}))}")
        
        # طباعة أهم النتائج
        if result.get('neurons'):
            logger.info("\n🧠 Top Neurons Generated:")
            for i, neuron in enumerate(result['neurons'][:5], 1):
                concept = neuron.get('concept', '')[:70]
                logger.info(f"   {i}. {concept}...")

    def show_status(self):
        """عرض حالة النظام الحالية"""
        logger.info("📊 System Status\n")
        
        # تحديث السياق
        self.context.update_from_trading()
        summary = self.context.get_summary()
        
        # حالة السوق
        logger.info("📊 Market & Trading:")
        logger.info(f"   Regime: {summary['state']['market_regime']}")
        logger.info(f"   Recent PnL (7d): {summary['state']['recent_pnl']:.2f}%")
        logger.info(f"   Win Rate (7d): {summary['state']['win_rate_7d']:.1%}")
        
        # حالة المعرفة
        logger.info("\n📚 Knowledge Base:")
        logger.info(f"   Total Beliefs: {summary['state']['active_neurons_count']}")
        logger.info(f"   Active Neurons: {len(self.context.get_active_neurons())}")
        
        # فجوات المعرفة
        if summary['knowledge_gaps']:
            logger.info("\n⚠️ Knowledge Gaps:")
            for i, gap in enumerate(summary['knowledge_gaps'][:3], 1):
                logger.info(f"   {i}. {gap}")
        
        # أنماط الخسائر
        if summary.get('losing_patterns'):
            logger.info("\n🔴 Losing Patterns:")
            for i, pattern in enumerate(summary['losing_patterns'][:3], 1):
                logger.info(f"   {i}. {pattern}")
        
        # توصية بالبحث
        if summary['should_research']:
            logger.info("\n🔍 Research Recommended:")
            for i, topic in enumerate(summary['priority_topics'][:3], 1):
                priority = summary['research_priorities'].get(topic, 0)
                logger.info(f"   {i}. {topic} (priority: {priority:.2f})")
        else:
            logger.info("\n✅ System performing well - no research needed")

    def show_stats(self):
        """إحصائيات النظام"""
        import sqlite3
        
        logger.info("📊 System Statistics\n")
        
        try:
            db_path = '/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # عدد beliefs
            cursor.execute('SELECT COUNT(*) FROM beliefs')
            total_beliefs = cursor.fetchone()[0]
            logger.info(f"📚 Total Beliefs: {total_beliefs:,}")
            
            # عدد neurons
            cursor.execute("SELECT COUNT(*) FROM beliefs WHERE key LIKE 'neuron:%'")
            total_neurons = cursor.fetchone()[0]
            logger.info(f"🧠 Total Neurons: {total_neurons:,}")
            
            # عدد learned items
            cursor.execute("SELECT COUNT(*) FROM beliefs WHERE key LIKE 'learned:%'")
            learned_items = cursor.fetchone()[0]
            logger.info(f"📚 Learned Items: {learned_items:,}")
            
            # Research results
            cursor.execute("SELECT COUNT(*) FROM beliefs WHERE key LIKE 'research_result:%'")
            research_count = cursor.fetchone()[0]
            logger.info(f"🔍 Research Sessions: {research_count:,}")
            
            # آخر 10 neurons
            logger.info("\n🧠 Recent Neurons:")
            cursor.execute("""
                SELECT value FROM beliefs 
                WHERE key LIKE 'neuron:research:%'
                ORDER BY updated_at DESC
                LIMIT 5
            """)
            
            for i, (value,) in enumerate(cursor.fetchall(), 1):
                try:
                    neuron = json.loads(value)
                    concept = neuron.get('concept', '')[:60]
                    logger.info(f"   {i}. {concept}...")
                except:
                    pass
            
            # آخر بحث
            logger.info("\n🔍 Recent Research:")
            cursor.execute("""
                SELECT value FROM beliefs 
                WHERE key LIKE 'research_result:%'
                ORDER BY updated_at DESC
                LIMIT 3
            """)
            
            for i, (value,) in enumerate(cursor.fetchall(), 1):
                try:
                    research = json.loads(value)
                    topic = research.get('topic', '')
                    neurons = research.get('neurons_generated', 0)
                    logger.info(f"   {i}. '{topic}' → {neurons} neurons")
                except:
                    pass
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error loading stats: {e}")


async def main():
    parser = argparse.ArgumentParser(
        description='Local Brain - الدماغ المحلي المتكامل',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--daemon', action='store_true',
                       help='تشغيل الدماغ كـ daemon مستمر')
    parser.add_argument('--once', action='store_true',
                       help='دورة تفكير واحدة فقط')
    parser.add_argument('--research', type=str,
                       help='بحث عن موضوع محدد')
    parser.add_argument('--status', action='store_true',
                       help='عرض حالة النظام')
    parser.add_argument('--stats', action='store_true',
                       help='عرض إحصائيات النظام')
    
    args = parser.parse_args()
    
    brain = LocalBrain()
    
    # Execute based on arguments
    if args.daemon:
        await brain.run_daemon()
    
    elif args.once:
        await brain.run_once()
    
    elif args.research:
        await brain.research_topic(args.research)
    
    elif args.status:
        brain.show_status()
    
    elif args.stats:
        brain.show_stats()
    
    else:
        # Default: show help + status
        parser.print_help()
        print("\n" + "="*70)
        brain.show_status()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")