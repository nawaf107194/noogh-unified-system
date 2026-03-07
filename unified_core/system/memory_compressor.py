# unified_core/system/memory_compressor.py

import sqlite3
from datetime import timedelta, datetime

class MemoryCompressor:
    def __init__(self, db_path):
        self.db_path = db_path

    def compress_memory(self, days_to_retain=90):
        """
        Compresses old episodic memories by retaining only the most recent data.
        
        :param days_to_retain: Number of days of memory to retain. Older entries will be deleted.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate the cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_to_retain)
        cutoff_timestamp = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Delete old entries
        delete_query = "DELETE FROM episodic_memory WHERE timestamp < ?"
        cursor.execute(delete_query, (cutoff_timestamp,))
        
        # Commit changes and close connection
        conn.commit()
        conn.close()

if __name__ == '__main__':
    db_path = 'path_to_your_sqlite_database.db'
    compressor = MemoryCompressor(db_path)
    compressor.compress_memory(days_to_retain=90)