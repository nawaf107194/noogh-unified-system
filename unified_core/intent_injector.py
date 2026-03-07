# unified_core/intent_injector.py
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("unified_core.intelligence.intent")

class IntentCoordinator:
    """منسق النوايا الذكي"""
    
    def __init__(self, db_path: str = "data/shared_memory.sqlite"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """تهيئة قاعدة البيانات"""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intent_type TEXT NOT NULL,
                priority REAL DEFAULT 0.5,
                payload TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def add_intent(self, intent_type: str, priority: float, payload: Dict):
        """إضافة نية جديدة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO intents (intent_type, priority, payload) VALUES (?, ?, ?)",
            (intent_type, priority, json.dumps(payload))
        )
        conn.commit()
        conn.close()
        logger.info(f"New intent added: {intent_type} (Priority: {priority})")

    def get_active(self) -> List[Dict]:
        """الحصول على النوايا النشطة"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM intents WHERE status = 'active' ORDER BY priority DESC")
        rows = cursor.fetchall()
        
        intents = []
        for row in rows:
            intent = dict(row)
            intent['payload'] = json.loads(intent['payload'])
            intents.append(intent)
            
        conn.close()
        return intents

class IntelligentIntentInjector:
    """واجهة حقن النوايا المتقدمة"""
    
    def __init__(self, db_path: str = "data/shared_memory.sqlite"):
        self.coordinator = IntentCoordinator(db_path)
        
    def inject(self, intent_type: str, weight: float, data: Dict):
        """حقن نية بوزن محدد"""
        self.coordinator.add_intent(intent_type, weight, data)
        
    def get_active_intents(self) -> List[Dict]:
        """استرجاع النوايا النشطة لمعالجتها"""
        return self.coordinator.get_active()

    def mark_completed(self, intent_id: int):
        """تحديد النية كمكتملة"""
        conn = sqlite3.connect(self.coordinator.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE intents SET status = 'completed', processed_at = ? WHERE id = ?",
            (datetime.now().isoformat(), intent_id)
        )
        conn.commit()
        conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NOOGH Intent Injector CLI")
    parser.add_argument("--type", required=True, help="Intent type (e.g., WISDOM_CHECK)")
    parser.add_argument("--priority", type=float, default=0.5, help="Priority (0.0-1.0)")
    parser.add_argument("--data", default="{}", help="JSON payload")
    
    args = parser.parse_args()
    
    try:
        payload = json.loads(args.data)
        injector = IntelligentIntentInjector()
        injector.inject(args.type, args.priority, payload)
        print(f"✅ Intent '{args.type}' injected successfully with priority {args.priority}")
    except Exception as e:
        print(f"❌ Failed to inject intent: {e}")
