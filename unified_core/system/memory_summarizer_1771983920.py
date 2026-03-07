# unified_core/system/memory_summarizer.py

import sqlite3
from datetime import datetime, timedelta

class MemorySummarizer:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def _connect_db(self):
        return sqlite3.connect(self.db_path)
    
    def summarize_memory(self, days_to_keep=90):
        """Compress and summarize old episodic memories."""
        conn = self._connect_db()
        cursor = conn.cursor()

        # Find the cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        # Summarize data
        cursor.execute("""
            INSERT INTO cognitive_journal (summary)
            SELECT 'Summary of events from ' || MIN(date) || ' to ' || MAX(date) || ': '
                || GROUP_CONCAT(event, ', ')
            FROM episodic_memory
            WHERE date < ?
        """, (cutoff_date,))
        
        # Delete old data
        cursor.execute("""
            DELETE FROM episodic_memory
            WHERE date < ?
        """, (cutoff_date,))

        conn.commit()
        conn.close()

if __name__ == '__main__':
    summarizer = MemorySummarizer('path_to_your_db.sqlite')
    summarizer.summarize_memory(days_to_keep=90)