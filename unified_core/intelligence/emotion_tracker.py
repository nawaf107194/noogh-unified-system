# unified_core/intelligence/emotion_tracker.py

import sqlite3
from typing import List, Dict

class EmotionTracker:
    def __init__(self, db_path: str = "path_to_your_sqlite_db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._initialize_table()

    def _initialize_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN,
                consecutive_successes INTEGER,
                consecutive_failures INTEGER
            )
        ''')
        self.conn.commit()

    def log_state(self, success: bool, consecutive_successes: int = 0, consecutive_failures: int = 0):
        self.cursor.execute('''
            INSERT INTO agent_states (success, consecutive_successes, consecutive_failures)
            VALUES (?, ?, ?)
        ''', (success, consecutive_successes, consecutive_failures))
        self.conn.commit()

    def get_last_state(self) -> Dict:
        self.cursor.execute('SELECT * FROM agent_states ORDER BY timestamp DESC LIMIT 1')
        return dict(self.cursor.fetchone()) if self.cursor.rowcount > 0 else {}

    def close(self):
        self.conn.close()