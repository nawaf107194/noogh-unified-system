# Goal Planning System - نظام تخطيط الأهداف
# يحلل الهدف الرئيسي ← يقسمه لأهداف فرعية ← يخطط خطوات العمل

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class Goal:
    """هدف واحد في النظام"""
    id: str
    description: str
    target_value: float
    current_value: float
    deadline: Optional[str] = None
    priority: float = 0.5  # 0-1
    status: str = 'active'  # active, completed, failed, paused
    parent_goal_id: Optional[str] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    @property
    def progress(self) -> float:
        """نسبة الإنجاز (0-1)"""
        if self.target_value == 0:
            return 0.0
        return min(self.current_value / self.target_value, 1.0)
    
    @property
    def is_complete(self) -> bool:
        """هل اكتمل الهدف؟"""
        return self.progress >= 1.0


@dataclass
class Action:
    """إجراء لتحقيق هدف"""
    id: str
    goal_id: str
    description: str
    action_type: str  # research, training, strategy_update, risk_adjustment
    parameters: Dict
    expected_impact: float  # 0-1
    status: str = 'pending'  # pending, in_progress, completed, failed
    created_at: str = None
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class GoalPlanner:
    """
    مخطط الأهداف - يحلل الأهداف الكبيرة ويقسمها لخطوات قابلة للتنفيذ.
    
    مثال:
    الهدف: "achieve 100% annual return with <10% drawdown"
    ↓
    أهداف فرعية:
    1. "improve win rate from 65% to 75%"
    2. "reduce average loss from 1% to 0.7%"
    3. "find 2 new uncorrelated strategies"
    ↓
    خطوات عمل لكل هدف فرعي
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = '/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite'
        
        self.db_path = Path(db_path)
        self._init_db()
        
        # الهدف الرئيسي (يمكن تغييره)
        self.main_goal = Goal(
            id='main_goal_2026',
            description='Achieve 100% annual return with max 10% drawdown',
            target_value=100.0,  # 100% return
            current_value=0.0,
            deadline=(datetime.now() + timedelta(days=365)).isoformat(),
            priority=1.0
        )
        
        logger.info("🎯 GoalPlanner initialized")
        logger.info(f"   Main Goal: {self.main_goal.description}")

    def _init_db(self):
        """إنشاء جداول الأهداف"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actions (
                id TEXT PRIMARY KEY,
                goal_id TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def decompose_goal(self, goal: Goal) -> List[Goal]:
        """
        تقسيم هدف كبير لأهداف فرعية.
        
        Args:
            goal: الهدف الرئيسي
            
        Returns:
            قائمة الأهداف الفرعية
        """
        logger.info(f"🔍 Decomposing goal: '{goal.description}'")
        
        subgoals = []
        
        # تحليل الهدف الرئيسي
        if "100% annual return" in goal.description:
            # Sub-goal 1: تحسين Win Rate
            subgoals.append(Goal(
                id=f"{goal.id}_winrate",
                description="Improve win rate from 65% to 75%",
                target_value=75.0,
                current_value=65.0,  # من Context
                deadline=goal.deadline,
                priority=0.9,
                parent_goal_id=goal.id
            ))
            
            # Sub-goal 2: تقليل الخسائر
            subgoals.append(Goal(
                id=f"{goal.id}_loss_reduction",
                description="Reduce average loss from 1.0% to 0.7%",
                target_value=0.7,
                current_value=1.0,
                deadline=goal.deadline,
                priority=0.85,
                parent_goal_id=goal.id
            ))
            
            # Sub-goal 3: استراتيجيات جديدة
            subgoals.append(Goal(
                id=f"{goal.id}_new_strategies",
                description="Find and deploy 2 new uncorrelated strategies",
                target_value=2.0,
                current_value=0.0,
                deadline=goal.deadline,
                priority=0.7,
                parent_goal_id=goal.id
            ))
            
            # Sub-goal 4: إدارة Drawdown
            subgoals.append(Goal(
                id=f"{goal.id}_drawdown",
                description="Keep max drawdown under 10%",
                target_value=10.0,
                current_value=5.0,  # الحالي أفضل
                deadline=goal.deadline,
                priority=0.95,
                parent_goal_id=goal.id
            ))
        
        # حفظ الأهداف الفرعية
        for subgoal in subgoals:
            self._save_goal(subgoal)
        
        logger.info(f"✅ Decomposed into {len(subgoals)} sub-goals")
        return subgoals

    def plan_actions(self, goal: Goal) -> List[Action]:
        """
        تخطيط الإجراءات لتحقيق هدف.
        
        Args:
            goal: الهدف المراد تحقيقه
            
        Returns:
            قائمة الإجراءات المطلوبة
        """
        logger.info(f"📋 Planning actions for: '{goal.description}'")
        
        actions = []
        
        # بناءً على نوع الهدف
        if "win rate" in goal.description.lower():
            # Action 1: بحث عن تقنيات
            actions.append(Action(
                id=f"{goal.id}_research_1",
                goal_id=goal.id,
                description="Research false signal reduction techniques",
                action_type="research",
                parameters={
                    "topic": "false signal reduction crypto trading",
                    "sources": ["arxiv", "github"]
                },
                expected_impact=0.3
            ))
            
            # Action 2: إضافة filters
            actions.append(Action(
                id=f"{goal.id}_strategy_1",
                goal_id=goal.id,
                description="Add multi-timeframe confirmation filter",
                action_type="strategy_update",
                parameters={
                    "filter_type": "multi_timeframe",
                    "timeframes": ["5m", "15m", "1h"]
                },
                expected_impact=0.25
            ))
            
            # Action 3: تدريب neurons
            actions.append(Action(
                id=f"{goal.id}_training_1",
                goal_id=goal.id,
                description="Train neurons on high-quality setups only",
                action_type="training",
                parameters={
                    "min_quality_score": 0.8,
                    "backtest_period": 30
                },
                expected_impact=0.2
            ))
        
        elif "loss" in goal.description.lower():
            # Action 1: تحسين Stop Loss
            actions.append(Action(
                id=f"{goal.id}_risk_1",
                goal_id=goal.id,
                description="Optimize stop loss placement using ATR",
                action_type="risk_adjustment",
                parameters={
                    "method": "atr_based",
                    "multiplier": 1.5
                },
                expected_impact=0.35
            ))
            
            # Action 2: بحث عن risk management
            actions.append(Action(
                id=f"{goal.id}_research_2",
                goal_id=goal.id,
                description="Research advanced risk management strategies",
                action_type="research",
                parameters={
                    "topic": "advanced risk management crypto",
                    "sources": ["youtube", "arxiv"]
                },
                expected_impact=0.25
            ))
        
        elif "strategies" in goal.description.lower():
            # Action 1: بحث عن استراتيجيات جديدة
            actions.append(Action(
                id=f"{goal.id}_research_3",
                goal_id=goal.id,
                description="Research uncorrelated trading strategies",
                action_type="research",
                parameters={
                    "topic": "uncorrelated crypto trading strategies",
                    "sources": ["github", "arxiv"]
                },
                expected_impact=0.4
            ))
            
            # Action 2: backtesting
            actions.append(Action(
                id=f"{goal.id}_training_2",
                goal_id=goal.id,
                description="Backtest and validate new strategy candidates",
                action_type="training",
                parameters={
                    "strategies": ["mean_reversion", "momentum"],
                    "period_days": 90
                },
                expected_impact=0.35
            ))
        
        elif "drawdown" in goal.description.lower():
            # Action 1: تحسين position sizing
            actions.append(Action(
                id=f"{goal.id}_risk_2",
                goal_id=goal.id,
                description="Implement Kelly Criterion for position sizing",
                action_type="risk_adjustment",
                parameters={
                    "method": "kelly",
                    "fraction": 0.25
                },
                expected_impact=0.4
            ))
        
        # حفظ الإجراءات
        for action in actions:
            self._save_action(action)
        
        logger.info(f"✅ Planned {len(actions)} actions")
        return actions

    def update_progress(self, goal_id: str, new_value: float):
        """تحديث تقدم الهدف"""
        goal = self._load_goal(goal_id)
        
        if goal:
            old_progress = goal.progress
            goal.current_value = new_value
            new_progress = goal.progress
            
            # تحديث الحالة
            if goal.is_complete:
                goal.status = 'completed'
            
            self._save_goal(goal)
            
            logger.info(f"📊 Goal '{goal.description[:40]}...' progress: {old_progress:.1%} → {new_progress:.1%}")
            
            # إذا اكتمل: تخطيط أهداف جديدة
            if goal.is_complete and goal.parent_goal_id:
                self._check_parent_goal_completion(goal.parent_goal_id)

    def _check_parent_goal_completion(self, parent_goal_id: str):
        """فحص إذا اكتملت كل الأهداف الفرعية"""
        subgoals = self._load_subgoals(parent_goal_id)
        
        all_complete = all(g.is_complete for g in subgoals)
        
        if all_complete:
            parent = self._load_goal(parent_goal_id)
            if parent:
                parent.status = 'completed'
                self._save_goal(parent)
                logger.info(f"🎉 PARENT GOAL COMPLETED: {parent.description}")

    def get_next_actions(self, max_actions: int = 3) -> List[Action]:
        """
        الإجراءات التالية ذات الأولوية.
        
        Returns:
            قائمة الإجراءات مرتبة حسب الأولوية
        """
        # جلب كل الإجراءات pending
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT data FROM actions
            WHERE json_extract(data, '$.status') = 'pending'
            ORDER BY json_extract(data, '$.expected_impact') DESC
        """)
        
        actions = []
        for (data,) in cursor.fetchall():
            action = Action(**json.loads(data))
            actions.append(action)
        
        conn.close()
        
        return actions[:max_actions]

    def execute_action(self, action: Action) -> bool:
        """
        تنفيذ إجراء.
        
        Returns:
            True إذا نجح، False إذا فشل
        """
        logger.info(f"▶️ Executing: {action.description}")
        
        action.status = 'in_progress'
        self._save_action(action)
        
        try:
            # تنفيذ بناءً على النوع
            if action.action_type == 'research':
                # TODO: استدعاء brain_research_orchestrator
                logger.info(f"   Research topic: {action.parameters['topic']}")
                success = True
            
            elif action.action_type == 'training':
                # TODO: استدعاء continuous_training_loop
                logger.info(f"   Training parameters: {action.parameters}")
                success = True
            
            elif action.action_type == 'strategy_update':
                # TODO: تحديث strategy
                logger.info(f"   Strategy update: {action.parameters}")
                success = True
            
            elif action.action_type == 'risk_adjustment':
                # TODO: تحديث risk settings
                logger.info(f"   Risk adjustment: {action.parameters}")
                success = True
            
            else:
                success = False
            
            # تحديث الحالة
            if success:
                action.status = 'completed'
                action.completed_at = datetime.now().isoformat()
                logger.info(f"   ✅ Action completed")
            else:
                action.status = 'failed'
                logger.warning(f"   ❌ Action failed")
            
            self._save_action(action)
            return success
            
        except Exception as e:
            logger.error(f"   ❌ Error executing action: {e}")
            action.status = 'failed'
            self._save_action(action)
            return False

    def get_progress_report(self) -> Dict:
        """تقرير شامل عن تقدم الأهداف"""
        report = {
            'main_goal': asdict(self.main_goal),
            'subgoals': [],
            'pending_actions': [],
            'completed_actions': 0,
            'overall_progress': 0.0
        }
        
        # جلب الأهداف الفرعية
        subgoals = self._load_subgoals(self.main_goal.id)
        report['subgoals'] = [asdict(g) for g in subgoals]
        
        # حساب التقدم الإجمالي
        if subgoals:
            report['overall_progress'] = sum(g.progress for g in subgoals) / len(subgoals)
        
        # الإجراءات التالية
        next_actions = self.get_next_actions(max_actions=5)
        report['pending_actions'] = [asdict(a) for a in next_actions]
        
        # عدد الإجراءات المكتملة
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM actions WHERE json_extract(data, '$.status') = 'completed'")
        report['completed_actions'] = cursor.fetchone()[0]
        conn.close()
        
        return report

    def _save_goal(self, goal: Goal):
        """حفظ هدف"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO goals (id, data, updated_at)
            VALUES (?, ?, ?)
        """, (goal.id, json.dumps(asdict(goal)), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    def _load_goal(self, goal_id: str) -> Optional[Goal]:
        """تحميل هدف"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT data FROM goals WHERE id = ?", (goal_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return Goal(**json.loads(row[0]))
        return None

    def _load_subgoals(self, parent_id: str) -> List[Goal]:
        """تحميل الأهداف الفرعية"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT data FROM goals
            WHERE json_extract(data, '$.parent_goal_id') = ?
        """, (parent_id,))
        
        subgoals = [Goal(**json.loads(row[0])) for row in cursor.fetchall()]
        
        conn.close()
        return subgoals

    def _save_action(self, action: Action):
        """حفظ إجراء"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO actions (id, goal_id, data)
            VALUES (?, ?, ?)
        """, (action.id, action.goal_id, json.dumps(asdict(action))))
        
        conn.commit()
        conn.close()


if __name__ == '__main__':
    # Test
    planner = GoalPlanner()
    
    # تقسيم الهدف الرئيسي
    subgoals = planner.decompose_goal(planner.main_goal)
    
    print("\n🎯 Sub-Goals:")
    for i, goal in enumerate(subgoals, 1):
        print(f"   {i}. {goal.description} (progress: {goal.progress:.1%})")
    
    # تخطيط إجراءات لأول هدف
    if subgoals:
        actions = planner.plan_actions(subgoals[0])
        
        print(f"\n📋 Actions for '{subgoals[0].description}':")
        for i, action in enumerate(actions, 1):
            print(f"   {i}. {action.description} (impact: {action.expected_impact:.1%})")
    
    # التقرير
    report = planner.get_progress_report()
    print(f"\n📊 Overall Progress: {report['overall_progress']:.1%}")