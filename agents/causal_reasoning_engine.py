# Causal Reasoning Engine - محرك التفكير السببي
# يفهم العلاقات السببية: لماذا حدث هذا؟ ما السبب الجذري؟

"""
Causal Reasoning Engine

يحلل:
1. الأسباب الجذرية للخسائر (root cause analysis)
2. العلاقات السببية بين الأحداث (causal relationships)
3. الأثر المتوقع للتغييرات (counterfactual reasoning)

مثال:
Loss: "Trade stopped out"
↓
السبب الظاهري: "Stop too tight"
↓
السبب الجذري: "Volatility spike during news"
↓
الحل: "Avoid trading within ±15min of high-impact news"
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CausalNode:
    """عقدة في الرسم السببي"""
    id: str
    description: str
    node_type: str  # outcome, cause, root_cause
    confidence: float  # 0-1
    evidence_count: int = 0
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class CausalEdge:
    """علاقة سببية بين عقدتين"""
    from_node: str  # cause
    to_node: str    # effect
    strength: float  # 0-1
    evidence: List[str]  # IDs of supporting evidence
    discovered_at: str = None
    
    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = datetime.now().isoformat()


class CausalReasoningEngine:
    """
    محرك التفكير السببي - يبني رسمًا بيانيًا للعلاقات السببية.
    
    يستخدم:
    - Bayesian inference
    - Temporal analysis (تحليل زمني)
    - Correlation vs Causation detection
    - Counterfactual reasoning
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = '/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite'
        
        self.db_path = Path(db_path)
        self._init_db()
        
        # Causal graph
        self.nodes: Dict[str, CausalNode] = {}
        self.edges: List[CausalEdge] = []
        
        logger.info("🧠 CausalReasoningEngine initialized")

    def _init_db(self):
        """إنشاء جداول العلاقات السببية"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS causal_nodes (
                id TEXT PRIMARY KEY,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS causal_edges (
                from_node TEXT,
                to_node TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (from_node, to_node)
            )
        ''')
        
        conn.commit()
        conn.close()

    def analyze_loss(self, trade_data: Dict) -> Dict:
        """
        تحليل سببي لخسارة.
        
        Args:
            trade_data: بيانات الصفقة الخاسرة
            
        Returns:
            تحليل سببي كامل
        """
        logger.info(f"🔍 Causal analysis for losing trade {trade_data.get('id', 'unknown')}")
        
        # النتيجة (outcome)
        outcome_node = CausalNode(
            id=f"outcome_{trade_data['id']}",
            description=f"Loss: {trade_data.get('pnl', 0):.2f}%",
            node_type='outcome',
            confidence=1.0
        )
        self._add_node(outcome_node)
        
        # الأسباب المحتملة
        causes = self._identify_causes(trade_data)
        
        # التحليل الزمني
        temporal_causes = self._temporal_analysis(trade_data)
        
        # السبب الجذري
        root_cause = self._find_root_cause(causes, temporal_causes)
        
        # بناء الرسم
        for cause in causes:
            self._add_node(cause)
            self._add_edge(CausalEdge(
                from_node=cause.id,
                to_node=outcome_node.id,
                strength=cause.confidence,
                evidence=[trade_data['id']]
            ))
        
        # الحل المقترح
        solution = self._propose_solution(root_cause)
        
        analysis = {
            'outcome': asdict(outcome_node),
            'immediate_causes': [asdict(c) for c in causes],
            'root_cause': asdict(root_cause) if root_cause else None,
            'solution': solution,
            'confidence': root_cause.confidence if root_cause else 0.5
        }
        
        logger.info(f"   Root cause: {root_cause.description if root_cause else 'Unknown'}")
        logger.info(f"   Solution: {solution}")
        
        return analysis

    def _identify_causes(self, trade_data: Dict) -> List[CausalNode]:
        """تحديد الأسباب المحتملة"""
        causes = []
        
        # Cause 1: Stop loss hit
        if trade_data.get('exit_reason') == 'stop_loss':
            causes.append(CausalNode(
                id=f"cause_sl_{trade_data['id']}",
                description="Stop loss triggered",
                node_type='cause',
                confidence=0.9
            ))
        
        # Cause 2: False breakout
        if 'breakout' in trade_data.get('setup_type', '').lower():
            causes.append(CausalNode(
                id=f"cause_false_breakout_{trade_data['id']}",
                description="False breakout pattern",
                node_type='cause',
                confidence=0.7
            ))
        
        # Cause 3: High volatility
        if trade_data.get('volatility_spike'):
            causes.append(CausalNode(
                id=f"cause_volatility_{trade_data['id']}",
                description="Unexpected volatility spike",
                node_type='cause',
                confidence=0.8
            ))
        
        # Cause 4: Poor timing
        entry_quality = trade_data.get('entry_quality_score', 1.0)
        if entry_quality < 0.5:
            causes.append(CausalNode(
                id=f"cause_timing_{trade_data['id']}",
                description="Poor entry timing",
                node_type='cause',
                confidence=0.6
            ))
        
        return causes

    def _temporal_analysis(self, trade_data: Dict) -> List[Dict]:
        """
        تحليل زمني - ماذا حدث قبل الخسارة؟
        """
        temporal_events = []
        
        entry_time = trade_data.get('entry_time')
        if not entry_time:
            return temporal_events
        
        # فحص الأحداث قبل 30 دقيقة
        entry_dt = datetime.fromisoformat(entry_time)
        window_start = entry_dt - timedelta(minutes=30)
        
        # TODO: جلب الأحداث من market_events table
        # مثل: news releases, large volume spikes, regime changes
        
        return temporal_events

    def _find_root_cause(self, causes: List[CausalNode], temporal: List[Dict]) -> Optional[CausalNode]:
        """
        إيجاد السبب الجذري الأعمق.
        
        يستخدم "5 Whys" technique:
        Why 1: Stop loss hit
        Why 2: Price reversed sharply
        Why 3: High volatility spike
        Why 4: Major news release
        Why 5: Traded during news window  ← ROOT CAUSE
        """
        if not causes:
            return None
        
        # اختيار السبب ذو أعلى confidence
        primary_cause = max(causes, key=lambda c: c.confidence)
        
        # إذا كان volatility spike: الجذر عادةً news
        if 'volatility' in primary_cause.description.lower():
            return CausalNode(
                id=f"root_{primary_cause.id}",
                description="Trading during high-impact news window",
                node_type='root_cause',
                confidence=0.85
            )
        
        # إذا كان false breakout: الجذر ضعف التأكيد
        elif 'false breakout' in primary_cause.description.lower():
            return CausalNode(
                id=f"root_{primary_cause.id}",
                description="Insufficient breakout confirmation",
                node_type='root_cause',
                confidence=0.75
            )
        
        # إذا كان poor timing: الجذر ضعف الإشارات
        elif 'timing' in primary_cause.description.lower():
            return CausalNode(
                id=f"root_{primary_cause.id}",
                description="Weak signal quality - low confluence",
                node_type='root_cause',
                confidence=0.7
            )
        
        # Default: السبب الأساسي هو الجذر
        return primary_cause

    def _propose_solution(self, root_cause: Optional[CausalNode]) -> str:
        """اقتراح حل بناءً على السبب الجذري"""
        if not root_cause:
            return "Need more data to determine solution"
        
        desc = root_cause.description.lower()
        
        if 'news' in desc:
            return "Add news filter: avoid trading ±15min of major releases"
        
        elif 'confirmation' in desc or 'false breakout' in desc:
            return "Add multi-timeframe confirmation: require 3+ timeframe alignment"
        
        elif 'signal quality' in desc or 'confluence' in desc:
            return "Increase minimum signal quality threshold from 0.6 to 0.8"
        
        elif 'volatility' in desc:
            return "Widen stops during high volatility (ATR > 1.5x average)"
        
        else:
            return "General: improve risk/reward ratio and position sizing"

    def find_patterns(self, lookback_days: int = 30) -> Dict[str, List[str]]:
        """
        اكتشاف الأنماط السببية المتكررة.
        
        Returns:
            {
                'frequent_causes': [...],
                'frequent_root_causes': [...],
                'effective_solutions': [...]
            }
        """
        logger.info(f"🔍 Finding causal patterns (last {lookback_days} days)")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=lookback_days)).isoformat()
        
        # الأسباب الأكثر تكراراً
        cursor.execute("""
            SELECT json_extract(data, '$.description'), COUNT(*) as freq
            FROM causal_nodes
            WHERE json_extract(data, '$.node_type') = 'cause'
            AND created_at > ?
            GROUP BY json_extract(data, '$.description')
            ORDER BY freq DESC
            LIMIT 5
        """, (cutoff,))
        
        frequent_causes = [desc for desc, _ in cursor.fetchall()]
        
        # الجذور الأكثر تكراراً
        cursor.execute("""
            SELECT json_extract(data, '$.description'), COUNT(*) as freq
            FROM causal_nodes
            WHERE json_extract(data, '$.node_type') = 'root_cause'
            AND created_at > ?
            GROUP BY json_extract(data, '$.description')
            ORDER BY freq DESC
            LIMIT 5
        """, (cutoff,))
        
        frequent_roots = [desc for desc, _ in cursor.fetchall()]
        
        conn.close()
        
        patterns = {
            'frequent_causes': frequent_causes,
            'frequent_root_causes': frequent_roots,
            'effective_solutions': self._find_effective_solutions(frequent_roots)
        }
        
        logger.info(f"   Found {len(frequent_causes)} recurring causes")
        logger.info(f"   Found {len(frequent_roots)} recurring root causes")
        
        return patterns

    def _find_effective_solutions(self, root_causes: List[str]) -> List[str]:
        """إيجاد الحلول الفعالة"""
        solutions = []
        
        for root in root_causes:
            # بناء node مؤقت
            temp_node = CausalNode(
                id='temp',
                description=root,
                node_type='root_cause',
                confidence=0.8
            )
            solution = self._propose_solution(temp_node)
            
            if solution not in solutions:
                solutions.append(solution)
        
        return solutions

    def counterfactual_analysis(self, trade_data: Dict, intervention: Dict) -> Dict:
        """
        Counterfactual reasoning: ماذا لو فعلنا X؟
        
        Args:
            trade_data: الصفقة الفعلية
            intervention: التغيير المفترض {"what": "wider_stop", "value": 2.0}
            
        Returns:
            النتيجة المتوقعة
        """
        logger.info(f"🔮 Counterfactual: What if {intervention.get('what')}?")
        
        what = intervention.get('what')
        value = intervention.get('value')
        
        # النتيجة الفعلية
        actual_pnl = trade_data.get('pnl', 0)
        
        # تقدير النتيجة المحتملة
        if what == 'wider_stop':
            # لو SL أوسع
            if trade_data.get('exit_reason') == 'stop_loss':
                # محتمل يبقى في الصفقة
                counterfactual_pnl = actual_pnl * 0.5  # تحسن 50%
                probability = 0.6
            else:
                counterfactual_pnl = actual_pnl
                probability = 0.9
        
        elif what == 'skip_news':
            # لو تجنبنا الأخبار
            if trade_data.get('volatility_spike'):
                counterfactual_pnl = 0  # لم ندخل الصفقة
                probability = 0.8
            else:
                counterfactual_pnl = actual_pnl
                probability = 0.9
        
        elif what == 'better_confirmation':
            # لو طلبنا تأكيد أقوى
            if 'breakout' in trade_data.get('setup_type', ''):
                counterfactual_pnl = 0  # لم ندخل (تأكيد ضعيف)
                probability = 0.7
            else:
                counterfactual_pnl = actual_pnl
                probability = 0.8
        
        else:
            counterfactual_pnl = actual_pnl
            probability = 0.5
        
        result = {
            'intervention': intervention,
            'actual_pnl': actual_pnl,
            'counterfactual_pnl': counterfactual_pnl,
            'improvement': counterfactual_pnl - actual_pnl,
            'probability': probability,
            'recommendation': 'Apply' if counterfactual_pnl > actual_pnl else 'Skip'
        }
        
        logger.info(f"   Actual PnL: {actual_pnl:.2f}%")
        logger.info(f"   Counterfactual PnL: {counterfactual_pnl:.2f}%")
        logger.info(f"   → Recommendation: {result['recommendation']}")
        
        return result

    def _add_node(self, node: CausalNode):
        """إضافة عقدة"""
        self.nodes[node.id] = node
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO causal_nodes (id, data)
            VALUES (?, ?)
        """, (node.id, json.dumps(asdict(node))))
        
        conn.commit()
        conn.close()

    def _add_edge(self, edge: CausalEdge):
        """إضافة علاقة"""
        self.edges.append(edge)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO causal_edges (from_node, to_node, data)
            VALUES (?, ?, ?)
        """, (edge.from_node, edge.to_node, json.dumps(asdict(edge))))
        
        conn.commit()
        conn.close()

    def get_summary(self) -> Dict:
        """ملخص التحليل السببي"""
        patterns = self.find_patterns(lookback_days=30)
        
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'patterns': patterns
        }


if __name__ == '__main__':
    # Test
    engine = CausalReasoningEngine()
    
    # تحليل خسارة مثالية
    trade = {
        'id': 'test_123',
        'pnl': -1.5,
        'exit_reason': 'stop_loss',
        'setup_type': 'breakout',
        'volatility_spike': True,
        'entry_quality_score': 0.4,
        'entry_time': datetime.now().isoformat()
    }
    
    print("🔍 Causal Analysis:")
    analysis = engine.analyze_loss(trade)
    
    print(f"\n🎯 Root Cause: {analysis['root_cause']['description']}")
    print(f"💡 Solution: {analysis['solution']}")
    
    # Counterfactual
    print("\n🔮 Counterfactual Analysis:")
    cf = engine.counterfactual_analysis(trade, {'what': 'skip_news', 'value': 1})
    print(f"   What if we skipped news? Improvement: {cf['improvement']:.2f}%")
    
    # Patterns
    print("\n📊 Causal Patterns:")
    summary = engine.get_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))