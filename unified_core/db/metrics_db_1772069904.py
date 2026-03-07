# unified_core/db/metrics_db.py

import time
from unified_core.db.router import DataRouter
from unified_core.db.postgres import PostgresManager

class MetricsDB:
    def __init__(self, db_config):
        self.db_router = DataRouter()
        self.pg_manager = PostgresManager(db_config)

    def store_metrics(self, cpu_usage, memory_usage, trade_volume):
        current_time = int(time.time())
        metrics_data = {
            'timestamp': current_time,
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'trade_volume': trade_volume
        }
        self.pg_manager.insert('metrics', metrics_data)

    def fetch_metrics(self, start_time, end_time):
        query = """
            SELECT * FROM metrics WHERE timestamp BETWEEN %s AND %s;
        """
        return self.pg_manager.fetch(query, (start_time, end_time))

# Example usage
if __name__ == '__main__':
    db_config = {
        'host': 'localhost',
        'user': 'user',
        'password': 'password',
        'database': 'metrics_db'
    }
    metrics_db = MetricsDB(db_config)
    
    # Store some metrics
    metrics_db.store_metrics(cpu_usage=50, memory_usage=75, trade_volume=1000)
    
    # Fetch and print stored metrics
    start_time = int(time.time()) - 3600  # One hour ago
    end_time = int(time.time())
    metrics = metrics_db.fetch_metrics(start_time, end_time)
    for metric in metrics:
        print(metric)