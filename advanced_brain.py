#!/usr/bin/env python3
# Advanced Brain - الدماغ المتقدم مع Goal Planning + Causal Reasoning
# الإصدار النهائي المتكامل

"""
Advanced Brain - الدماغ المتقدم

يدمج:
1. UnifiedBrainDaemon (البحث المستمر)
2. GoalPlanner (تخطيط الأهداف)
3. CausalReasoningEngine (التحليل السببي)

الحلقة الكاملة:
Trading → Loss → Causal Analysis → Root Cause → Goal Planning → Actions → Research → Neurons → Training → Strategy → Trading

الاستخدام:
  python3 advanced_brain.py --daemon       # تشغيل كامل
  python3 advanced_brain.py --once         # دورة واحدة
  python3 advanced_brain.py --analyze      # تحليل وضع النظام
  python3 advanced_brain.py --goals        # عرض الأهداف
"""

import asyncio
import argparse
import logging
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.unified_context import UnifiedContext
from agents.unified_brain_daemon import UnifiedBrainDaemon
from agents.goal_planner import GoalPlanner, Goal, Action
from agents.causal_reasoning_engine import CausalReasoningEngine
from agents.brain_research_orchestrator import brain_think_and_research

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdvancedBrain:
    """
    الدماغ المتقدم - يجمع كل القدرات في نظام واحد.
    """

    def __init__(self):
        # Core components
        self.context = UnifiedContext()
        self.daemon = UnifiedBrainDaemon()
        self.goal_planner = GoalPlanner()
        self.causal_engine = CausalReasoningEngine()
        
        logger.info("🧠 AdvancedBrain initialized")
        logger.info("   ✓ UnifiedContext")
        logger.info("   ✓ UnifiedBrainDaemon")
        logger.info("   ✓ GoalPlanner")
        logger.info("   ✓ CausalReasoningEngine")

    async def enhanced_think_cycle(self):
        """
        دورة تفكير محسّنة مع Goal Planning + Causal Analysis.
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🧠 ENHANCED THINK CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"{'='*70}\n")
        
        try:
            # ① تحديث السياق
            logger.info("📊 Step 1: Updating Context...")
            self.context.update_from_trading()
            summary = self.context.get_summary()
            
            logger.info(f"   PnL: {summary['state']['recent_pnl']:.2f}%")
            logger.info(f"   Win Rate: {summary['state']['win_rate_7d']:.1%}")
            
            # ② تحليل سببي للخسائر الأخيرة
            logger.info("\n🔍 Step 2: Causal Analysis of Recent Losses...")
            recent_losses = await self._get_recent_losses()
            
            root_causes = []
            for loss in recent_losses[:3]:  # آخر 3 خسائر
                analysis = self.causal_engine.analyze_loss(loss)
                if analysis['root_cause']:
                    root_causes.append(analysis)
                    logger.info(f"   🎯 Root: {analysis['root_cause']['description']}")
                    logger.info(f"   💡 Solution: {analysis['solution']}")
            
            # ③ تحديث الأهداف بناءً على التحليل
            logger.info("\n🎯 Step 3: Goal Planning...")
            
            # تقسيم الهدف الرئيسي إذا لم يتم
            subgoals = self.goal_planner._load_subgoals(self.goal_planner.main_goal.id)
            if not subgoals:
                logger.info("   Decomposing main goal...")
                subgoals = self.goal_planner.decompose_goal(self.goal_planner.main_goal)
            
            # تخطيط إجراءات بناءً على root causes
            for analysis in root_causes:
                solution = analysis['solution']
                logger.info(f"   Planning action: {solution}")
                
                # إضافة action للهدف المناسب
                self._add_solution_action(solution, subgoals)
            
            # ④ تنفيذ الإجراءات التالية
            logger.info("\n▶️ Step 4: Executing Priority Actions...")
            next_actions = self.goal_planner.get_next_actions(max_actions=2)
            
            for action in next_actions:
                logger.info(f"   Executing: {action.description}")
                success = await self._execute_action_enhanced(action)
                
                if success:
                    logger.info(f"      ✅ Success")
                else:
                    logger.info(f"      ❌ Failed")
            
            # ⑤ تحديث تقدم الأهداف
            logger.info("\n📊 Step 5: Updating Goal Progress...")
            await self._update_goal_progress()
            
            # ⑥ عرض التقرير
            report = self.goal_planner.get_progress_report()
            logger.info(f"\n📈 Overall Progress: {report['overall_progress']:.1%}")
            logger.info(f"   Completed Actions: {report['completed_actions']}")
            logger.info(f"   Pending Actions: {len(report['pending_actions'])}")
            
            logger.info(f"\n{'='*70}")
            logger.info("✅ ENHANCED CYCLE COMPLETE")
            logger.info(f"{'='*70}\n")
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced cycle: {e}", exc_info=True)

    async def _get_recent_losses(self) -> list:
        """جلب آخر الخسائر"""
        import sqlite3
        
        try:
            conn = sqlite3.connect(self.context.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT value FROM beliefs 
                WHERE key LIKE 'trade:%'
                AND json_extract(value, '$.pnl') < 0
                ORDER BY updated_at DESC
                LIMIT 5
            """)
            
            losses = [json.loads(row[0]) for row in cursor.fetchall()]
            conn.close()
            
            return losses
            
        except Exception as e:
            logger.warning(f"Could not fetch losses: {e}")
            return []

    def _add_solution_action(self, solution: str, subgoals: list):
        """إضافة إجراء بناءً على الحل المقترح"""
        # تحديد نوع الإجراء
        if 'filter' in solution.lower() or 'news' in solution.lower():
            action_type = 'strategy_update'
            goal_id = f"{self.goal_planner.main_goal.id}_winrate"  # يحسّن win rate
        
        elif 'confirmation' in solution.lower():
            action_type = 'strategy_update'
            goal_id = f"{self.goal_planner.main_goal.id}_winrate"
        
        elif 'signal quality' in solution.lower():
            action_type = 'research'
            goal_id = f"{self.goal_planner.main_goal.id}_winrate"
        
        elif 'stop' in solution.lower() or 'risk' in solution.lower():
            action_type = 'risk_adjustment'
            goal_id = f"{self.goal_planner.main_goal.id}_loss_reduction"
        
        else:
            action_type = 'strategy_update'
            goal_id = subgoals[0].id if subgoals else self.goal_planner.main_goal.id
        
        # إنشاء الإجراء
        action = Action(
            id=f"action_{datetime.now().timestamp()}",
            goal_id=goal_id,
            description=solution,
            action_type=action_type,
            parameters={'solution': solution},
            expected_impact=0.3
        )
        
        self.goal_planner._save_action(action)

    async def _execute_action_enhanced(self, action: Action) -> bool:
        """تنفيذ إجراء مع تكامل كامل"""
        try:
            if action.action_type == 'research':
                # استخراج topic من description
                topic = action.parameters.get('topic', action.description)
                
                result = await brain_think_and_research(
                    topic=topic,
                    sources=['youtube', 'github', 'arxiv'],
                    generate_neurons=True
                )
                
                return result.get('neurons_generated', 0) > 0
            
            elif action.action_type == 'training':
                # TODO: تكامل مع ContinuousTrainingLoop
                logger.info(f"      Training: {action.parameters}")
                return True
            
            elif action.action_type == 'strategy_update':
                # TODO: تحديث AdvancedStrategy
                logger.info(f"      Strategy update: {action.parameters}")
                return True
            
            elif action.action_type == 'risk_adjustment':
                # TODO: تحديث Risk settings
                logger.info(f"      Risk adjustment: {action.parameters}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return False

    async def _update_goal_progress(self):
        """تحديث تقدم الأهداف بناءً على البيانات الفعلية"""
        # تحديث Win Rate goal
        win_rate = self.context.state.win_rate_7d * 100
        self.goal_planner.update_progress(
            goal_id=f"{self.goal_planner.main_goal.id}_winrate",
            new_value=win_rate
        )
        
        # تحديث PnL goal (إذا كان إيجابي)
        if self.context.state.recent_pnl > 0:
            self.goal_planner.update_progress(
                goal_id=self.goal_planner.main_goal.id,
                new_value=self.context.state.recent_pnl
            )

    def analyze_system(self):
        """تحليل شامل للنظام"""
        logger.info("🔍 ADVANCED SYSTEM ANALYSIS\n")
        
        # Context
        logger.info("📊 System Context:")
        self.context.update_from_trading()
        summary = self.context.get_summary()
        logger.info(f"   Market Regime: {summary['state']['market_regime']}")
        logger.info(f"   Recent PnL: {summary['state']['recent_pnl']:.2f}%")
        logger.info(f"   Win Rate: {summary['state']['win_rate_7d']:.1%}")
        
        # Goals
        logger.info("\n🎯 Goal Progress:")
        report = self.goal_planner.get_progress_report()
        logger.info(f"   Overall Progress: {report['overall_progress']:.1%}")
        logger.info(f"   Main Goal: {report['main_goal']['description']}")
        
        if report['subgoals']:
            logger.info("\n   Sub-Goals:")
            for i, sg in enumerate(report['subgoals'], 1):
                progress = sg['current_value'] / sg['target_value'] if sg['target_value'] > 0 else 0
                logger.info(f"      {i}. {sg['description']} ({progress:.1%})")
        
        # Causal Patterns
        logger.info("\n🔍 Causal Patterns (Last 30 days):")
        causal_summary = self.causal_engine.get_summary()
        patterns = causal_summary['patterns']
        
        if patterns['frequent_root_causes']:
            logger.info("   Recurring Root Causes:")
            for i, cause in enumerate(patterns['frequent_root_causes'], 1):
                logger.info(f"      {i}. {cause}")
        
        if patterns['effective_solutions']:
            logger.info("\n   Recommended Solutions:")
            for i, solution in enumerate(patterns['effective_solutions'], 1):
                logger.info(f"      {i}. {solution}")
        
        # Next Actions
        logger.info("\n▶️ Next Priority Actions:")
        next_actions = self.goal_planner.get_next_actions(max_actions=5)
        for i, action in enumerate(next_actions, 1):
            logger.info(f"   {i}. {action.description} (impact: {action.expected_impact:.1%})")

    def show_goals(self):
        """عرض الأهداف والتقدم"""
        logger.info("🎯 GOAL TRACKING\n")
        
        report = self.goal_planner.get_progress_report()
        
        # Main goal
        logger.info(f"🎯 Main Goal:")
        logger.info(f"   {report['main_goal']['description']}")
        logger.info(f"   Progress: {report['overall_progress']:.1%}")
        logger.info(f"   Status: {report['main_goal']['status']}")
        
        # Sub-goals
        if report['subgoals']:
            logger.info(f"\n📈 Sub-Goals ({len(report['subgoals'])}):")
            for i, sg in enumerate(report['subgoals'], 1):
                progress = sg['current_value'] / sg['target_value'] if sg['target_value'] > 0 else 0
                status_emoji = "✅" if sg['status'] == 'completed' else "🟡" if progress > 0.5 else "🔴"
                
                logger.info(f"\n   {status_emoji} {i}. {sg['description']}")
                logger.info(f"      Progress: {progress:.1%} ({sg['current_value']:.1f}/{sg['target_value']:.1f})")
                logger.info(f"      Priority: {sg['priority']:.1f}")
                logger.info(f"      Status: {sg['status']}")
        
        # Actions summary
        logger.info(f"\n📋 Actions:")
        logger.info(f"   Completed: {report['completed_actions']}")
        logger.info(f"   Pending: {len(report['pending_actions'])}")

    async def run_daemon(self):
        """تشغيل الدماغ المتقدم كـ daemon"""
        logger.info("\n" + "#"*70)
        logger.info("# ADVANCED BRAIN DAEMON STARTED")
        logger.info(f"# Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("#"*70 + "\n")
        
        cycle_interval = 1800  # 30 min
        
        try:
            while True:
                await self.enhanced_think_cycle()
                
                logger.info(f"💤 Sleeping for {cycle_interval}s ({cycle_interval//60}min)...\n")
                await asyncio.sleep(cycle_interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Daemon stopped")


async def main():
    parser = argparse.ArgumentParser(
        description='Advanced Brain - الدماغ المتقدم',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--daemon', action='store_true',
                       help='تشغيل daemon مستمر')
    parser.add_argument('--once', action='store_true',
                       help='دورة واحدة')
    parser.add_argument('--analyze', action='store_true',
                       help='تحليل النظام')
    parser.add_argument('--goals', action='store_true',
                       help='عرض الأهداف')
    
    args = parser.parse_args()
    
    brain = AdvancedBrain()
    
    if args.daemon:
        await brain.run_daemon()
    
    elif args.once:
        await brain.enhanced_think_cycle()
    
    elif args.analyze:
        brain.analyze_system()
    
    elif args.goals:
        brain.show_goals()
    
    else:
        parser.print_help()
        print("\n" + "="*70)
        brain.analyze_system()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")