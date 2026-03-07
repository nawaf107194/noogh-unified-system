# unified_core/db/candle_storage.py

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict

class CandleStorage:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._initialize_table()

    def _initialize_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS candles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL
        );
        """
        self.db_manager.execute(query)

    def add_candle(self, timestamp: datetime, open_price: float, high_price: float, low_price: float, close_price: float, volume: float):
        query = "INSERT INTO candles (timestamp, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?);"
        self.db_manager.execute(query, (timestamp, open_price, high_price, low_price, close_price, volume))

    def get_candles_by_timeframe(self, start: datetime, end: datetime) -> List[Dict]:
        query = "SELECT * FROM candles WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp ASC;"
        results = self.db_manager.query(query, (start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S')))
        return [dict(row) for row in results]

    def get_latest_candle(self) -> Dict:
        query = "SELECT * FROM candles ORDER BY timestamp DESC LIMIT 1;"
        result = self.db_manager.query(query)
        return dict(result[0]) if result else None

if __name__ == '__main__':
    # Example usage
    from unified_core.db.router import DataRouter

    class MockDBManager:
        def execute(self, query, params=None):
            print(f"Executing: {query} with params {params}")

        def query(self, query, params=None):
            print(f"Querying: {query} with params {params}")
            return []

    db_manager = MockDBManager()
    candle_storage = CandleStorage(db_manager)

    # Adding a candle
    now = datetime.now()
    candle_storage.add_candle(now, 100.0, 105.0, 98.0, 102.0, 5000.0)

    # Fetching candles within a timeframe
    start_time = now - timedelta(days=1)
    end_time = now
    candles = candle_storage.get_candles_by_timeframe(start_time, end_time)
    print("Candles:", candles)

    # Getting the latest candle
    latest_candle = candle_storage.get_latest_candle()
    print("Latest Candle:", latest_candle)