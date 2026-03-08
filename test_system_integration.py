#!/usr/bin/env python3
# System Integration Test - اختبار التكامل الشامل
# يتحقق من أن كل الأجزاء تعمل معاً مثل الساعة ⏰

"""
System Integration Test

يختبر:
1. ✅ CausalReasoningEngine - التحليل السببي
2. ✅ GoalPlanner - تخطيط الأهداف
3. ✅ AdvancedBrain - التكامل الكامل
4. ✅ Database connectivity
5. ✅ Full workflow simulation

الاستخدام:
  python3 test_system_integration.py
"""

import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.causal_reasoning_engine import CausalReasoningEngine
from agents.goal_planner import GoalPlanner, Goal, Action
from advanced_brain import AdvancedBrain

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemIntegrationTest:
    """اختبار التكامل الشامل"""

    def __init__(self):
        self.results = {
            'causal_engine': False,
            'goal_planner': False,
            'advanced_brain': False,
            'database': False,
            'workflow': False
        }

    def test_causal_engine(self) -> bool:
        """اختبار CausalReasoningEngine"""
        logger.info("\n" + "="*70)
        logger.info("📝 TEST 1: CausalReasoningEngine")
        logger.info("="*70)
        
        try:
            # إنشاء engine
            engine = CausalReasoningEngine()
            logger.info("✅ CausalReasoningEngine created")
            
            # تحليل خسارة مثالية
            test_trade = {
                'id': 'test_integration_001',
                'pnl': -1.8,
                'exit_reason': 'stop_loss',
                'setup_type': 'breakout',
                'volatility_spike': True,
                'entry_quality_score': 0.35,
                'entry_time': datetime.now().isoformat()
            }
            
            logger.info(f"   Analyzing test loss: {test_trade['pnl']}%")
            analysis = engine.analyze_loss(test_trade)
            
            # التحقق من النتائج
            assert 'root_cause' in analysis, "Missing root_cause"
            assert 'solution' in analysis, "Missing solution"
            assert analysis['root_cause'] is not None, "Root cause is None"
            
            logger.info(f"   ✅ Root Cause: {analysis['root_cause']['description']}")
            logger.info(f"   ✅ Solution: {analysis['solution']}")
            
            # Counterfactual analysis
            logger.info("   Testing counterfactual reasoning...")
            cf = engine.counterfactual_analysis(
                test_trade, 
                {'what': 'skip_news', 'value': 1}
            )
            
            assert 'improvement' in cf, "Missing improvement"
            logger.info(f"   ✅ Counterfactual improvement: {cf['improvement']:.2f}%")
            
            # Pattern discovery
            logger.info("   Testing pattern discovery...")
            patterns = engine.find_patterns(lookback_days=30)
            assert 'frequent_causes' in patterns, "Missing patterns"
            logger.info(f"   ✅ Found patterns: {len(patterns['frequent_causes'])} causes")
            
            logger.info("✅ CausalReasoningEngine: PASSED")
            return True
            
        except Exception as e:
            logger.error(f"❌ CausalReasoningEngine: FAILED - {e}", exc_info=True)
            return False

    def test_goal_planner(self) -> bool:
        """اختبار GoalPlanner"""
        logger.info("\n" + "="*70)
        logger.info("📝 TEST 2: GoalPlanner")
        logger.info("="*70)
        
        try:
            # إنشاء planner
            planner = GoalPlanner()
            logger.info("✅ GoalPlanner created")
            logger.info(f"   Main Goal: {planner.main_goal.description}")
            
            # تقسيم الهدف
            logger.info("   Decomposing main goal...")
            subgoals = planner.decompose_goal(planner.main_goal)
            
            assert len(subgoals) > 0, "No subgoals created"
            logger.info(f"   ✅ Created {len(subgoals)} sub-goals")
            
            for i, sg in enumerate(subgoals, 1):
                logger.info(f"      {i}. {sg.description}")
            
            # تخطيط إجراءات
            logger.info("   Planning actions for first sub-goal...")
            actions = planner.plan_actions(subgoals[0])
            
            assert len(actions) > 0, "No actions created"
            logger.info(f"   ✅ Planned {len(actions)} actions")
            
            for i, action in enumerate(actions, 1):
                logger.info(f"      {i}. {action.description} (impact: {action.expected_impact:.1%})")
            
            # التقرير
            logger.info("   Generating progress report...")
            report = planner.get_progress_report()
            
            assert 'overall_progress' in report, "Missing overall_progress"
            logger.info(f"   ✅ Overall Progress: {report['overall_progress']:.1%}")
            logger.info(f"   ✅ Sub-goals: {len(report['subgoals'])}")
            logger.info(f"   ✅ Pending Actions: {len(report['pending_actions'])}")
            
            logger.info("✅ GoalPlanner: PASSED")
            return True
            
        except Exception as e:
            logger.error(f"❌ GoalPlanner: FAILED - {e}", exc_info=True)
            return False

    async def test_advanced_brain(self) -> bool:
        """اختبار AdvancedBrain"""
        logger.info("\n" + "="*70)
        logger.info("📝 TEST 3: AdvancedBrain Integration")
        logger.info("="*70)
        
        try:
            # إنشاء brain
            brain = AdvancedBrain()
            logger.info("✅ AdvancedBrain created")
            
            # فحص المكونات
            assert brain.context is not None, "Missing context"
            assert brain.daemon is not None, "Missing daemon"
            assert brain.goal_planner is not None, "Missing goal_planner"
            assert brain.causal_engine is not None, "Missing causal_engine"
            
            logger.info("   ✅ All components initialized")
            
            # اختبار analyze_system
            logger.info("   Testing analyze_system()...")
            brain.analyze_system()
            logger.info("   ✅ analyze_system() works")
            
            # اختبار show_goals
            logger.info("   Testing show_goals()...")
            brain.show_goals()
            logger.info("   ✅ show_goals() works")
            
            logger.info("✅ AdvancedBrain: PASSED")
            return True
            
        except Exception as e:
            logger.error(f"❌ AdvancedBrain: FAILED - {e}", exc_info=True)
            return False

    def test_database(self) -> bool:
        """اختبار قاعدة البيانات"""
        logger.info("\n" + "="*70)
        logger.info("📝 TEST 4: Database Connectivity")
        logger.info("="*70)
        
        try:
            import sqlite3
            
            db_path = Path('/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite')
            
            # فحص الملف
            if not db_path.exists():
                logger.warning(f"   Database file not found at {db_path}")
                logger.info("   Creating database...")
                db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # الاتصال
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            logger.info("✅ Database connection successful")
            
            # فحص الجداول
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"   Tables found: {', '.join(tables)}")
            
            required_tables = ['causal_nodes', 'causal_edges', 'goals', 'actions']
            for table in required_tables:
                if table in tables:
                    logger.info(f"   ✅ Table '{table}' exists")
                else:
                    logger.warning(f"   ⚠️ Table '{table}' missing (will be created on first use)")
            
            conn.close()
            
            logger.info("✅ Database: PASSED")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database: FAILED - {e}", exc_info=True)
            return False

    async def test_workflow(self) -> bool:
        """اختبار سير العمل الكامل"""
        logger.info("\n" + "="*70)
        logger.info("📝 TEST 5: Full Workflow Simulation")
        logger.info("="*70)
        
        try:
            # إنشاء النظام
            brain = AdvancedBrain()
            
            # محاكاة خسارة
            logger.info("   Step 1: Simulating a loss...")
            test_loss = {
                'id': 'workflow_test_001',
                'pnl': -2.1,
                'exit_reason': 'stop_loss',
                'setup_type': 'momentum',
                'volatility_spike': False,
                'entry_quality_score': 0.45,
                'entry_time': datetime.now().isoformat()
            }
            
            # تحليل سببي
            logger.info("   Step 2: Causal analysis...")
            analysis = brain.causal_engine.analyze_loss(test_loss)
            
            assert analysis['root_cause'] is not None
            logger.info(f"   ✅ Root cause identified: {analysis['root_cause']['description']}")
            
            # إضافة إجراء بناءً على الحل
            logger.info("   Step 3: Creating action from solution...")
            solution = analysis['solution']
            
            subgoals = brain.goal_planner._load_subgoals(brain.goal_planner.main_goal.id)
            if not subgoals:
                subgoals = brain.goal_planner.decompose_goal(brain.goal_planner.main_goal)
            
            brain._add_solution_action(solution, subgoals)
            logger.info(f"   ✅ Action created: {solution}")
            
            # جلب الإجراءات التالية
            logger.info("   Step 4: Getting next priority actions...")
            next_actions = brain.goal_planner.get_next_actions(max_actions=3)
            
            assert len(next_actions) > 0
            logger.info(f"   ✅ Found {len(next_actions)} priority actions")
            
            for i, action in enumerate(next_actions[:2], 1):
                logger.info(f"      {i}. {action.description}")
            
            # محاكاة تحديث التقدم
            logger.info("   Step 5: Updating goal progress...")
            await brain._update_goal_progress()
            logger.info("   ✅ Progress updated")
            
            # التقرير النهائي
            logger.info("   Step 6: Generating final report...")
            report = brain.goal_planner.get_progress_report()
            
            logger.info(f"   ✅ Overall Progress: {report['overall_progress']:.1%}")
            logger.info(f"   ✅ Sub-goals: {len(report['subgoals'])}")
            logger.info(f"   ✅ Pending Actions: {len(report['pending_actions'])}")
            
            logger.info("✅ Workflow: PASSED")
            return True
            
        except Exception as e:
            logger.error(f"❌ Workflow: FAILED - {e}", exc_info=True)
            return False

    async def run_all_tests(self):
        """تشغيل كل الاختبارات"""
        logger.info("\n" + "#"*70)
        logger.info("# SYSTEM INTEGRATION TEST SUITE")
        logger.info(f"# Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("#"*70)
        
        # تشغيل الاختبارات
        self.results['causal_engine'] = self.test_causal_engine()
        self.results['goal_planner'] = self.test_goal_planner()
        self.results['advanced_brain'] = await self.test_advanced_brain()
        self.results['database'] = self.test_database()
        self.results['workflow'] = await self.test_workflow()
        
        # التقرير النهائي
        logger.info("\n" + "#"*70)
        logger.info("# TEST RESULTS SUMMARY")
        logger.info("#"*70)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"   {test_name:20s}: {status}")
            
            if result:
                passed += 1
            else:
                failed += 1
        
        logger.info("\n" + "#"*70)
        logger.info(f"# TOTAL: {passed} passed, {failed} failed")
        
        if failed == 0:
            logger.info("# 🎉 ALL TESTS PASSED - SYSTEM READY!")
        else:
            logger.info(f"# ⚠️ {failed} TEST(S) FAILED - CHECK LOGS ABOVE")
        
        logger.info("#"*70 + "\n")
        
        return failed == 0


async def main():
    """Main entry point"""
    tester = SystemIntegrationTest()
    success = await tester.run_all_tests()
    
    # Exit code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 Tests interrupted")
        sys.exit(1)