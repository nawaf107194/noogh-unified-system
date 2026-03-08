# Unified Context - السياق الموحد للنظام
# يشارك بين كل الوكلاء لضمان التناسق

import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class SystemState:
    """حالة النظام الحالية"""
    timestamp: str
    market_regime: str  # trending/ranging/volatile/choppy
    recent_pnl: float
    win_rate_7d: float
    drawdown: float
    active_neurons_count: int
    learning_rate: float


class UnifiedContext:
    """
    السياق الموحد - مركز المعلومات لكل الوكلاء.
    
    يوفر:
    - حالة التداول الحالية
    - الأنماط الخاسرة الأخيرة
    - فجوات المعرفة
    - أولويات البحث
    - neurons النشطة
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or '/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite'
        self.state = self._load_current_state()
        self.losing_patterns: List[str] = []
        self.knowledge_gaps: List[str] = []
        self.research_priorities: Dict[str, float] = {}  # topic -> priority score
        
        logger.info("🎯 UnifiedContext initialized")

    def _load_current_state(self) -> SystemState:
        """تحميل حالة النظام من البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # آخر 7 أيام من PnL
            cursor.execute("""
                SELECT json_extract(value, '$.pnl') 
                FROM beliefs 
                WHERE key LIKE 'trade:%' 
                AND updated_at > datetime('now', '-7 days')
            """)
            
            pnls = [float(row[0]) for row in cursor.fetchall() if row[0]]
            recent_pnl = sum(pnls) if pnls else 0.0
            win_rate = len([p for p in pnls if p > 0]) / len(pnls) if pnls else 0.0
            
            # عدد neurons النشطة
            cursor.execute("SELECT COUNT(*) FROM beliefs WHERE key LIKE 'neuron:%'")
            neuron_count = cursor.fetchone()[0]
            
            conn.close()
            
            return SystemState(
                timestamp=datetime.now().isoformat(),
                market_regime="unknown",  # سيتم تحديثه من RegimeDetector
                recent_pnl=recent_pnl,
                win_rate_7d=win_rate,
                drawdown=min(pnls) if pnls else 0.0,
                active_neurons_count=neuron_count,
                learning_rate=0.5
            )
            
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return SystemState(
                timestamp=datetime.now().isoformat(),
                market_regime="unknown",
                recent_pnl=0.0,
                win_rate_7d=0.0,
                drawdown=0.0,
                active_neurons_count=0,
                learning_rate=0.5
            )

    def update_from_trading(self):
        """تحديث السياق من بيانات التداول"""
        self.state = self._load_current_state()
        self._update_losing_patterns()
        self._update_knowledge_gaps()
        self._calculate_research_priorities()
        
        logger.info(f"📊 Context updated: PnL={self.state.recent_pnl:.2f}, WinRate={self.state.win_rate_7d:.1%}")

    def _update_losing_patterns(self):
        """تحديد الأنماط الخاسرة الأخيرة"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # آخر 10 خسائر
            cursor.execute("""
                SELECT json_extract(value, '$.reason'), json_extract(value, '$.setup_type')
                FROM beliefs 
                WHERE key LIKE 'trade:%' 
                AND json_extract(value, '$.pnl') < 0
                ORDER BY updated_at DESC
                LIMIT 10
            """)
            
            patterns = {}
            for reason, setup in cursor.fetchall():
                if reason:
                    patterns[reason] = patterns.get(reason, 0) + 1
            
            conn.close()
            
            # أكثر 3 أنماط تكراراً
            self.losing_patterns = sorted(patterns.keys(), key=lambda k: patterns[k], reverse=True)[:3]
            
        except Exception as e:
            logger.warning(f"Could not update losing patterns: {e}")
            self.losing_patterns = []

    def _update_knowledge_gaps(self):
        """تحديد فجوات المعرفة"""
        gaps = []
        
        # Gap 1: Win rate منخفض
        if self.state.win_rate_7d < 0.6:
            gaps.append("improve win rate techniques")
        
        # Gap 2: Drawdown كبير
        if self.state.drawdown < -5.0:
            gaps.append("risk management drawdown recovery")
        
        # Gap 3: أنماط خاسرة متكررة
        if self.losing_patterns:
            for pattern in self.losing_patterns[:2]:
                gaps.append(f"avoid {pattern} in trading")
        
        # Gap 4: Regime جديد
        if self.state.market_regime in ['volatile', 'choppy']:
            gaps.append(f"trading strategies for {self.state.market_regime} market")
        
        self.knowledge_gaps = gaps

    def _calculate_research_priorities(self):
        """حساب أولويات البحث"""
        priorities = {}
        
        for gap in self.knowledge_gaps:
            # Priority score based on urgency
            if "drawdown" in gap or "loss" in gap:
                score = 1.0  # أعلى أولوية
            elif "win rate" in gap:
                score = 0.8
            elif "avoid" in gap:
                score = 0.7
            else:
                score = 0.5
            
            priorities[gap] = score
        
        # ترتيب حسب الأولوية
        self.research_priorities = dict(
            sorted(priorities.items(), key=lambda x: x[1], reverse=True)
        )

    def should_research(self) -> bool:
        """هل نحتاج بحث الآن؟"""
        return (
            len(self.knowledge_gaps) > 0 or
            self.state.recent_pnl < -3.0 or  # خسارة > 3%
            self.state.win_rate_7d < 0.5  # win rate < 50%
        )

    def priority_topics(self, max_topics: int = 3) -> List[str]:
        """أعلى مواضيع البحث أولوية"""
        return list(self.research_priorities.keys())[:max_topics]

    def get_active_neurons(self) -> List[Dict]:
        """جلب neurons النشطة"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT key, value 
                FROM beliefs 
                WHERE key LIKE 'neuron:research:%'
                ORDER BY updated_at DESC
                LIMIT 10
            """)
            
            neurons = []
            for key, value in cursor.fetchall():
                try:
                    neurons.append(json.loads(value))
                except:
                    pass
            
            conn.close()
            return neurons
            
        except Exception as e:
            logger.error(f"Error loading neurons: {e}")
            return []

    def record_research_outcome(self, topic: str, success: bool, impact: float):
        """تسجيل نتيجة بحث (لـ meta-learning)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            outcome = {
                'topic': topic,
                'success': success,
                'impact': impact,
                'timestamp': datetime.now().isoformat()
            }
            
            cursor.execute("""
                INSERT INTO beliefs (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (
                f"research_outcome:{datetime.now().timestamp()}",
                json.dumps(outcome),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error recording outcome: {e}")

    def get_summary(self) -> Dict:
        """ملخص الحالة الحالية"""
        return {
            'state': asdict(self.state),
            'losing_patterns': self.losing_patterns,
            'knowledge_gaps': self.knowledge_gaps,
            'research_priorities': self.research_priorities,
            'should_research': self.should_research(),
            'priority_topics': self.priority_topics()
        }

    def __repr__(self):
        return f"UnifiedContext(regime={self.state.market_regime}, pnl={self.state.recent_pnl:.2f}, gaps={len(self.knowledge_gaps)})"


if __name__ == '__main__':
    # Test
    context = UnifiedContext()
    context.update_from_trading()
    
    print("\n📊 System Context:")
    print(json.dumps(context.get_summary(), indent=2, ensure_ascii=False))
    
    if context.should_research():
        print("\n🔍 Research Needed:")
        for topic in context.priority_topics():
            print(f"   - {topic} (priority: {context.research_priorities[topic]})")