#!/usr/bin/env python3
"""
Data Models - نماذج البيانات

ORM models for:
- Trades
- Market Data (OHLCV)
- Signals
- Performance Metrics
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Trade(Base):
    """صفقة تداول"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Trade info
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # LONG/SHORT
    entry_price = Column(Float, nullable=False)
    entry_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Exit info
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime, nullable=True)
    exit_reason = Column(String(20), nullable=True)  # TP/SL/MANUAL
    
    # Risk management
    sl_price = Column(Float, nullable=False)
    tp_price = Column(Float, nullable=False)
    position_size = Column(Float, nullable=False)  # in USDT
    leverage = Column(Integer, default=1)
    
    # Performance
    pnl = Column(Float, nullable=True)  # P&L in USDT
    pnl_pct = Column(Float, nullable=True)  # P&L in %
    duration_minutes = Column(Integer, nullable=True)
    
    # Strategy info
    strategy_name = Column(String(50), nullable=False)
    strategy_version = Column(String(20), nullable=False)
    
    # Signal info
    technical_score = Column(Float, nullable=True)
    confidence = Column(String(20), nullable=True)  # HIGH/MEDIUM/LOW
    signal_data = Column(JSON, nullable=True)  # Full signal details
    
    # Status
    status = Column(String(20), nullable=False, default='OPEN')  # OPEN/CLOSED
    is_paper_trade = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_symbol_time', 'symbol', 'entry_time'),
        Index('idx_status_time', 'status', 'entry_time'),
        Index('idx_strategy', 'strategy_name', 'strategy_version'),
    )
    
    def __repr__(self):
        return f"<Trade(id={self.id}, symbol={self.symbol}, side={self.side}, status={self.status})>"


class MarketData(Base):
    """بيانات السوق (OHLCV)"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d
    timestamp = Column(DateTime, nullable=False, index=True)
    
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    # Additional metrics
    quote_volume = Column(Float, nullable=True)  # Volume in quote asset (USDT)
    trades_count = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_symbol_timeframe_ts', 'symbol', 'timeframe', 'timestamp', unique=True),
    )
    
    def __repr__(self):
        return f"<MarketData(symbol={self.symbol}, timeframe={self.timeframe}, timestamp={self.timestamp})>"


class Signal(Base):
    """إشارة تداول"""
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Signal details
    direction = Column(String(10), nullable=False)  # LONG/SHORT/NEUTRAL
    confidence = Column(Float, nullable=False)  # 0-100
    
    # Entry levels
    entry_price = Column(Float, nullable=False)
    sl_price = Column(Float, nullable=True)  # NULL when signal is skipped
    tp_price = Column(Float, nullable=True)  # NULL when signal is skipped
    
    # Technical analysis
    technical_score = Column(Float, nullable=False)  # 0-100
    rsi = Column(Float, nullable=True)
    macd_signal = Column(String(20), nullable=True)
    ma_signal = Column(String(20), nullable=True)
    patterns = Column(JSON, nullable=True)  # List of detected patterns
    support_resistance = Column(JSON, nullable=True)
    
    # Market context
    volatility = Column(Float, nullable=True)
    volume_surge = Column(Float, nullable=True)
    trend_strength = Column(String(20), nullable=True)  # STRONG/MODERATE/WEAK
    
    # Action taken
    action_taken = Column(String(20), nullable=False, default='NONE')  # ENTERED/SKIPPED/NONE
    skip_reason = Column(String(100), nullable=True)
    
    # Link to trade
    trade_id = Column(Integer, nullable=True)  # If trade was opened
    
    # Strategy
    strategy_name = Column(String(50), nullable=False)
    engine_version = Column(String(20), nullable=False)
    
    # Full data
    full_analysis = Column(JSON, nullable=True)  # Complete analysis dump
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_signal_symbol_time', 'symbol', 'timestamp'),
        Index('idx_signal_action', 'action_taken', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Signal(id={self.id}, symbol={self.symbol}, direction={self.direction}, confidence={self.confidence})>"


class PerformanceMetrics(Base):
    """مقاييس الأداء اليومية"""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    date = Column(DateTime, nullable=False, unique=True, index=True)
    strategy_name = Column(String(50), nullable=False)
    
    # Trade stats
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    
    # Performance
    win_rate = Column(Float, default=0.0)
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    
    # P&L
    total_pnl = Column(Float, default=0.0)
    total_pnl_pct = Column(Float, default=0.0)
    
    # Risk metrics
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)
    
    # Execution
    avg_trade_duration = Column(Integer, nullable=True)  # minutes
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<PerformanceMetrics(date={self.date}, win_rate={self.win_rate:.2%})>"


class StrategyConfig(Base):
    """إعدادات الإستراتيجية"""
    __tablename__ = 'strategy_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    strategy_name = Column(String(50), nullable=False)
    version = Column(String(20), nullable=False)
    
    # Config as JSON
    config = Column(JSON, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_strategy_version', 'strategy_name', 'version', unique=True),
    )
    
    def __repr__(self):
        return f"<StrategyConfig(strategy={self.strategy_name}, version={self.version})>"
