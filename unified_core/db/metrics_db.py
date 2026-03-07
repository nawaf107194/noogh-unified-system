# unified_core/db/metrics_db.py

from unified_core.db.vector_db import VectorDBManager
from unified_core.db.router import DataRouter
import datetime

class MetricsDB:
    def __init__(self):
        self.data_router = DataRouter()
        self.metrics_db_manager = VectorDBManager(db_name="metrics")

    def _get_current_timestamp(self):
        return datetime.datetime.now().isoformat()

    def store_metric(self, metric_name, value):
        timestamp = self._get_current_timestamp()
        data = {
            "timestamp": timestamp,
            "metric_name": metric_name,
            "value": value
        }
        self.metrics_db_manager.insert(data)

    def get_metrics_by_range(self, start_time, end_time):
        query = f"SELECT * FROM metrics WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'"
        return self.metrics_db_manager.query(query)

if __name__ == '__main__':
    metrics_db = MetricsDB()
    metrics_db.store_metric("CPU_usage", 75)
    print(metrics_db.get_metrics_by_range("2023-10-01T00:00:00Z", "2023-10-02T00:00:00Z"))