# unified_core/db/query_optimizer.py

from unified_core.db.memory_store import MemoryStore
import sqlite3

class QueryOptimizer:
    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store
        self.conn = memory_store.get_connection()
        self.cursor = self.conn.cursor()

    def index_hot_columns(self, table_name, columns):
        for column in columns:
            query = f"CREATE INDEX idx_{table_name}_{column} ON {table_name}({column})"
            self.cursor.execute(query)
        self.conn.commit()

if __name__ == '__main__':
    # Example usage
    memory_store = MemoryStore()
    optimizer = QueryOptimizer(memory_store)
    optimizer.index_hot_columns('beliefs', ['confidence', 'timestamp'])