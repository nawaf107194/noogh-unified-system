#!/usr/bin/env python3
"""
Database Layer - طبقة قاعدة البيانات

Supports:
- SQLite (development)
- PostgreSQL (production)
- Connection pooling
- Transaction management
- Migration support
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


class Database:
    """قاعدة بيانات موحدة"""
    
    _instance: Optional['Database'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.engine = None
        self.SessionLocal = None
        self._configure()
    
    def _configure(self):
        """Configure database connection"""
        db_type = os.getenv('DB_TYPE', 'sqlite')
        
        if db_type == 'postgresql':
            db_url = self._build_postgres_url()
            pool_config = {
                'poolclass': QueuePool,
                'pool_size': 10,
                'max_overflow': 20,
                'pool_pre_ping': True,
                'pool_recycle': 3600
            }
        else:
            # SQLite (default)
            db_path = os.getenv('DB_PATH', 'data/noogh_trading.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            db_url = f'sqlite:///{db_path}'
            pool_config = {
                'connect_args': {'check_same_thread': False}
            }
        
        logger.info(f"🔌 Connecting to database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
        
        self.engine = create_engine(db_url, **pool_config, echo=False)
        
        # Enable WAL mode for SQLite (better concurrency)
        if db_type == 'sqlite':
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info("✅ Database configured")
    
    def _build_postgres_url(self) -> str:
        """Build PostgreSQL connection URL"""
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        user = os.getenv('DB_USER', 'noogh')
        password = os.getenv('DB_PASSWORD', '')
        database = os.getenv('DB_NAME', 'noogh_trading')
        
        return f'postgresql://{user}:{password}@{host}:{port}/{database}'
    
    @contextmanager
    def session(self) -> Session:
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Database error: {e}")
            raise
        finally:
            session.close()
    
    def create_all(self, base):
        """Create all tables"""
        base.metadata.create_all(bind=self.engine)
        logger.info("✅ All tables created")
    
    def drop_all(self, base):
        """Drop all tables (use with caution!)"""
        base.metadata.drop_all(bind=self.engine)
        logger.warning("⚠️ All tables dropped")
    
    def execute_raw(self, sql: str, params: Dict[str, Any] = None):
        """Execute raw SQL"""
        with self.session() as session:
            result = session.execute(sql, params or {})
            return result.fetchall()


# Singleton instance
_db = Database()


def get_db() -> Database:
    """Get database instance"""
    return _db


def get_session() -> Session:
    """Get database session (use with context manager)"""
    return _db.SessionLocal()
