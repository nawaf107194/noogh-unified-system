import sqlite3
from datetime import datetime, timedelta

class MemorySummarizer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.setup()

    def setup(self):
        # Create table if not exists
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_summary (
                id INTEGER PRIMARY KEY,
                summary TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def summarize_memory(self, user_id, episode_id, new_memories):
        # Fetch existing summaries for the user and episode
        self.cursor.execute('SELECT summary FROM memory_summary WHERE user_id=? AND episode_id=?', (user_id, episode_id))
        existing_summaries = self.cursor.fetchall()
        
        # Combine new memories with existing summaries
        combined_summaries = [summary[0] for summary in existing_summaries if summary[0]]
        for mem in new_memories:
            if mem not in combined_summaries:
                combined_summaries.append(mem)
        
        # Create a single summary from the list of summaries
        final_summary = "\n".join(combined_summaries)
        
        # Update or insert the summary into the database
        self.cursor.execute('''
            INSERT OR REPLACE INTO memory_summary (user_id, episode_id, summary) VALUES (?, ?, ?)
        ''', (user_id, episode_id, final_summary))
        self.conn.commit()

    def get_latest_summary(self, user_id, episode_id):
        # Fetch the latest summary for the user and episode
        self.cursor.execute('SELECT summary FROM memory_summary WHERE user_id=? AND episode_id=? ORDER BY created_at DESC LIMIT 1', (user_id, episode_id))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def close(self):
        self.conn.close()

if __name__ == '__main__':
    db_path = 'path_to_your_memory_db.sqlite'
    summarizer = MemorySummarizer(db_path)
    
    # Example usage
    user_id = 123
    episode_id = 456
    new_memories = ["memory1", "memory2", "memory3"]
    
    summarizer.summarize_memory(user_id, episode_id, new_memories)
    
    latest_summary = summarizer.get_latest_summary(user_id, episode_id)
    print("Latest Summary:", latest_summary)
    
    summarizer.close()