#!/usr/bin/env python3
"""
Market Data Repository - مستودع بيانات السوق

CRUD operations for OHLCV data
"""

from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session

from data.models import MarketData
from data.database import get_db

import logging
logger = logging.getLogger(__name__)


class MarketDataRepository:
    """مستودع بيانات السوق"""
    
    def __init__(self):
        self.db = get_db()
    
    def bulk_insert(self, symbol: str, timeframe: str, df: pd.DataFrame) -> int:
        """إدخال جماعي للبيانات"""
        with self.db.session() as session:
            count = 0
            for _, row in df.iterrows():
                # Check if exists
                exists = session.query(MarketData).filter(
                    MarketData.symbol == symbol,
                    MarketData.timeframe == timeframe,
                    MarketData.timestamp == row['timestamp']
                ).first()
                
                if not exists:
                    data = MarketData(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=row['timestamp'],
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume']
                    )
                    session.add(data)
                    count += 1
            
            if count > 0:
                logger.info(f"✅ Inserted {count} candles for {symbol} {timeframe}")
            
            return count
    
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 500
    ) -> pd.DataFrame:
        """جلب بيانات OHLCV"""
        with self.db.session() as session:
            query = session.query(MarketData).filter(
                MarketData.symbol == symbol,
                MarketData.timeframe == timeframe
            )
            
            if start_time:
                query = query.filter(MarketData.timestamp >= start_time)
            if end_time:
                query = query.filter(MarketData.timestamp <= end_time)
            
            query = query.order_by(MarketData.timestamp.desc()).limit(limit)
            data = query.all()
            
            if not data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'timestamp': d.timestamp,
                'open': d.open,
                'high': d.high,
                'low': d.low,
                'close': d.close,
                'volume': d.volume
            } for d in data])
            
            # Sort by timestamp ascending
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df
    
    def get_latest_timestamp(self, symbol: str, timeframe: str) -> Optional[datetime]:
        """جلب آخر timestamp محفوظ"""
        with self.db.session() as session:
            latest = session.query(MarketData).filter(
                MarketData.symbol == symbol,
                MarketData.timeframe == timeframe
            ).order_by(MarketData.timestamp.desc()).first()
            
            return latest.timestamp if latest else None
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """حذف البيانات القديمة"""
        with self.db.session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted = session.query(MarketData).filter(
                MarketData.timestamp < cutoff_date
            ).delete()
            
            if deleted > 0:
                logger.info(f"✅ Deleted {deleted} old candles")
            
            return deleted
