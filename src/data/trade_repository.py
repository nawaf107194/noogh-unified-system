#!/usr/bin/env python3
"""
Trade Repository - مستودع الصفقات

CRUD operations for trades
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from data.models import Trade, Signal, PerformanceMetrics
from data.database import get_db

import logging
logger = logging.getLogger(__name__)


class TradeRepository:
    """مستودع الصفقات"""
    
    def __init__(self):
        self.db = get_db()
    
    def create(self, trade_data: Dict[str, Any]) -> Trade:
        """إنشاء صفقة جديدة"""
        with self.db.session() as session:
            trade = Trade(**trade_data)
            session.add(trade)
            session.flush()
            session.refresh(trade)
            logger.info(f"✅ Trade created: {trade.id} - {trade.symbol} {trade.side}")
            return trade
    
    def get_by_id(self, trade_id: int) -> Optional[Trade]:
        """جلب صفقة بالمعرف"""
        with self.db.session() as session:
            return session.query(Trade).filter(Trade.id == trade_id).first()
    
    def get_open_trades(self, symbol: Optional[str] = None) -> List[Trade]:
        """جلب الصفقات المفتوحة"""
        with self.db.session() as session:
            query = session.query(Trade).filter(Trade.status == 'OPEN')
            if symbol:
                query = query.filter(Trade.symbol == symbol)
            return query.all()
    
    def update(self, trade_id: int, update_data: Dict[str, Any]) -> Optional[Trade]:
        """تحديث صفقة"""
        with self.db.session() as session:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if trade:
                for key, value in update_data.items():
                    setattr(trade, key, value)
                trade.updated_at = datetime.utcnow()
                session.flush()
                logger.info(f"✅ Trade updated: {trade_id}")
            return trade
    
    def close_trade(self, trade_id: int, exit_price: float, exit_reason: str) -> Optional[Trade]:
        """إغلاق صفقة"""
        with self.db.session() as session:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                return None
            
            # Calculate P&L
            if trade.side == 'LONG':
                pnl_pct = ((exit_price - trade.entry_price) / trade.entry_price) * 100
            else:  # SHORT
                pnl_pct = ((trade.entry_price - exit_price) / trade.entry_price) * 100
            
            pnl_usd = (trade.position_size * pnl_pct / 100) * trade.leverage
            
            # Duration
            duration = (datetime.utcnow() - trade.entry_time).total_seconds() / 60
            
            # Update trade
            trade.exit_price = exit_price
            trade.exit_time = datetime.utcnow()
            trade.exit_reason = exit_reason
            trade.pnl = pnl_usd
            trade.pnl_pct = pnl_pct
            trade.duration_minutes = int(duration)
            trade.status = 'CLOSED'
            
            session.flush()
            logger.info(f"✅ Trade closed: {trade_id} - P&L: {pnl_pct:+.2f}% ({exit_reason})")
            
            return trade
    
    def get_trades(
        self,
        symbol: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Trade]:
        """جلب صفقات بفلاتر"""
        with self.db.session() as session:
            query = session.query(Trade)
            
            if symbol:
                query = query.filter(Trade.symbol == symbol)
            if status:
                query = query.filter(Trade.status == status)
            if start_date:
                query = query.filter(Trade.entry_time >= start_date)
            if end_date:
                query = query.filter(Trade.entry_time <= end_date)
            
            query = query.order_by(Trade.entry_time.desc()).limit(limit)
            return query.all()
    
    def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        strategy_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """حساب إحصائيات"""
        with self.db.session() as session:
            query = session.query(Trade).filter(Trade.status == 'CLOSED')
            
            if start_date:
                query = query.filter(Trade.entry_time >= start_date)
            if strategy_name:
                query = query.filter(Trade.strategy_name == strategy_name)
            
            trades = query.all()
            
            if not trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0,
                    'avg_pnl': 0.0
                }
            
            winning = [t for t in trades if t.pnl and t.pnl > 0]
            losing = [t for t in trades if t.pnl and t.pnl < 0]
            
            total_wins = sum(t.pnl for t in winning)
            total_losses = abs(sum(t.pnl for t in losing)) if losing else 0.001
            
            return {
                'total_trades': len(trades),
                'winning_trades': len(winning),
                'losing_trades': len(losing),
                'win_rate': len(winning) / len(trades) if trades else 0.0,
                'profit_factor': total_wins / total_losses if total_losses > 0 else 0.0,
                'total_pnl': sum(t.pnl for t in trades if t.pnl),
                'avg_win': total_wins / len(winning) if winning else 0.0,
                'avg_loss': -total_losses / len(losing) if losing else 0.0,
                'avg_duration': sum(t.duration_minutes for t in trades if t.duration_minutes) / len(trades) if trades else 0
            }
    
    def delete(self, trade_id: int) -> bool:
        """حذف صفقة (استخدم بحذر)"""
        with self.db.session() as session:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if trade:
                session.delete(trade)
                logger.warning(f"⚠️ Trade deleted: {trade_id}")
                return True
            return False
