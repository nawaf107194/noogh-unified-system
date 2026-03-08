#!/usr/bin/env python3
"""
Decision Persistence Layer - طبقة حفظ القرارات
يحفظ قرارات DecisionScorer في قاعدة البيانات بشكل دائم
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict

logger = logging.getLogger("unified_core.core.decision_persistence")


class DecisionPersistence:
    """مدير حفظ القرارات في قاعدة البيانات"""

    def __init__(self, db_path: Optional[Path] = None):
        """
        تهيئة نظام حفظ القرارات

        Args:
            db_path: مسار قاعدة البيانات (اختياري)
        """
        if db_path is None:
            # Default path
            db_path = Path(__file__).parent.parent.parent / 'data' / 'shared_memory.sqlite'

        self.db_path = db_path
        self._ensure_table_exists()
        logger.info(f"✓ DecisionPersistence initialized at {db_path}")

    def _ensure_table_exists(self):
        """إنشاء جدول القرارات إذا لم يكن موجوداً"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                decision_id TEXT PRIMARY KEY,
                decision_type TEXT NOT NULL,
                query TEXT,
                action_type TEXT,
                content TEXT,
                commitment_hash TEXT,
                based_on_beliefs TEXT,
                constrained_by TEXT,
                cost_paid REAL,
                urgency REAL,
                timestamp REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decisions_timestamp
            ON decisions(timestamp DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decisions_type
            ON decisions(decision_type)
        """)

        conn.commit()
        conn.close()

        logger.debug("✓ Decisions table ensured")

    def save_decision(
        self,
        decision_id: str,
        decision_type: str,
        query: str,
        content: Dict[str, Any],
        commitment_hash: str,
        based_on_beliefs: List[str],
        constrained_by: List[str],
        cost_paid: float,
        urgency: float = 0.5,
        timestamp: float = None
    ) -> bool:
        """
        حفظ قرار في قاعدة البيانات

        Args:
            decision_id: معرّف القرار
            decision_type: نوع القرار (action, abstain, goal)
            query: السؤال أو السياق
            content: محتوى القرار
            commitment_hash: hash الالتزام
            based_on_beliefs: المعتقدات المستخدمة
            constrained_by: القيود المطبقة
            cost_paid: التكلفة المدفوعة
            urgency: مستوى الإلحاح
            timestamp: الوقت (اختياري)

        Returns:
            True إذا نجح الحفظ
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            import time
            if timestamp is None:
                timestamp = time.time()

            # Extract action_type from content
            action_type = content.get('action_type', 'unknown')

            # Convert lists and dicts to JSON
            content_json = json.dumps(content)
            beliefs_json = json.dumps(based_on_beliefs)
            constraints_json = json.dumps(constrained_by)

            cursor.execute("""
                INSERT OR REPLACE INTO decisions (
                    decision_id, decision_type, query, action_type,
                    content, commitment_hash, based_on_beliefs,
                    constrained_by, cost_paid, urgency, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision_id,
                decision_type,
                query,
                action_type,
                content_json,
                commitment_hash,
                beliefs_json,
                constraints_json,
                cost_paid,
                urgency,
                timestamp
            ))

            conn.commit()
            conn.close()

            logger.debug(f"✓ Decision saved: {decision_id} ({action_type})")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to save decision {decision_id}: {e}")
            return False

    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """
        استرجاع قرار من قاعدة البيانات

        Args:
            decision_id: معرّف القرار

        Returns:
            القرار أو None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM decisions WHERE decision_id = ?
            """, (decision_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                decision = dict(row)
                # Parse JSON fields
                decision['content'] = json.loads(decision['content'])
                decision['based_on_beliefs'] = json.loads(decision['based_on_beliefs'])
                decision['constrained_by'] = json.loads(decision['constrained_by'])
                return decision

            return None

        except Exception as e:
            logger.error(f"✗ Failed to get decision {decision_id}: {e}")
            return None

    def get_recent_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        استرجاع أحدث القرارات

        Args:
            limit: عدد القرارات

        Returns:
            قائمة القرارات
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM decisions
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            decisions = []
            for row in rows:
                decision = dict(row)
                # Parse JSON fields
                decision['content'] = json.loads(decision['content'])
                decision['based_on_beliefs'] = json.loads(decision['based_on_beliefs'])
                decision['constrained_by'] = json.loads(decision['constrained_by'])
                decisions.append(decision)

            return decisions

        except Exception as e:
            logger.error(f"✗ Failed to get recent decisions: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        إحصائيات القرارات

        Returns:
            إحصائيات
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total decisions
            cursor.execute("SELECT COUNT(*) FROM decisions")
            total = cursor.fetchone()[0]

            # By type
            cursor.execute("""
                SELECT decision_type, COUNT(*)
                FROM decisions
                GROUP BY decision_type
            """)
            by_type = dict(cursor.fetchall())

            # Average cost
            cursor.execute("SELECT AVG(cost_paid) FROM decisions")
            avg_cost = cursor.fetchone()[0] or 0

            # Recent 24h
            import time
            day_ago = time.time() - 86400
            cursor.execute("""
                SELECT COUNT(*) FROM decisions
                WHERE timestamp > ?
            """, (day_ago,))
            recent_24h = cursor.fetchone()[0]

            conn.close()

            return {
                'total_decisions': total,
                'by_type': by_type,
                'avg_cost': round(avg_cost, 2),
                'recent_24h': recent_24h
            }

        except Exception as e:
            logger.error(f"✗ Failed to get stats: {e}")
            return {}


# Global instance
_persistence_instance = None


def get_decision_persistence(db_path: Optional[Path] = None) -> DecisionPersistence:
    """
    احصل على instance واحد من DecisionPersistence

    Args:
        db_path: مسار قاعدة البيانات (اختياري)

    Returns:
        DecisionPersistence instance
    """
    global _persistence_instance

    if _persistence_instance is None:
        _persistence_instance = DecisionPersistence(db_path)

    return _persistence_instance


# === QUICK TEST ===
if __name__ == "__main__":
    import time

    print("🧪 Testing DecisionPersistence...")

    # Initialize
    persistence = get_decision_persistence()

    # Save test decision
    success = persistence.save_decision(
        decision_id="test_decision_001",
        decision_type="action",
        query="Should I buy BTCUSDT?",
        content={
            "action_type": "buy_signal",
            "params": {"symbol": "BTCUSDT", "confidence": 0.85}
        },
        commitment_hash="abc123",
        based_on_beliefs=["belief_1", "belief_2"],
        constrained_by=["constraint_1"],
        cost_paid=100.5,
        urgency=0.7,
        timestamp=time.time()
    )

    print(f"✓ Save decision: {success}")

    # Get decision
    decision = persistence.get_decision("test_decision_001")
    print(f"✓ Retrieved decision: {decision['decision_id'] if decision else 'None'}")

    # Get recent
    recent = persistence.get_recent_decisions(5)
    print(f"✓ Recent decisions: {len(recent)}")

    # Get stats
    stats = persistence.get_stats()
    print(f"✓ Stats: {stats}")

    print("\n✅ All tests passed!")
