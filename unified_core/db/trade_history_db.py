# unified_core/db/trade_history_db.py

import json
from .router import DataRouter

class TradeHistoryDB:
    """
    Time-series storage interface for trade history using DataRouter.
    """
    def __init__(self, data_router: DataRouter):
        self.router = data_router

    async def insert_candle(self, timestamp, symbol, open_price, high_price, low_price, close_price, volume):
        # We store trade history as relational entries in postgres via DataRouter
        query = {
            "expression": "INSERT INTO trade_history (timestamp, symbol, open, high, low, close, volume) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            "params": [timestamp, symbol, open_price, high_price, low_price, close_price, volume]
        }
        await self.router.execute_postgres(query, operation="insert", params={})

    async def get_candles(self, symbol, start_time=None, end_time=None):
        query = f"SELECT * FROM trade_history WHERE symbol='{symbol}'"
        if start_time and end_time:
            query += f" AND timestamp BETWEEN '{start_time}' AND '{end_time}'"
            
        result = await self.router.query(query)
        if result.success and result.sql_result:
            return result.sql_result.rows
        return []