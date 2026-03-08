#!/usr/bin/env python3
"""
Database Initialization - إنشاء قاعدة البيانات

ينشئ:
- الجداول
- الفهارس
- يتحقق من الاتصال
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data import get_db, Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database(drop_existing: bool = False):
    """إنشاء قاعدة البيانات"""
    logger.info("🔧 Initializing database...")
    
    db = get_db()
    
    if drop_existing:
        logger.warning("⚠️  Dropping existing tables...")
        db.drop_all(Base)
    
    # Create all tables
    db.create_all(Base)
    
    logger.info("✅ Database initialized successfully!")
    logger.info("")
    logger.info("Tables created:")
    logger.info("  - trades")
    logger.info("  - market_data")
    logger.info("  - signals")
    logger.info("  - performance_metrics")
    logger.info("  - strategy_configs")
    logger.info("")
    
    # Test connection
    logger.info("🔍 Testing database connection...")
    try:
        from data import TradeRepository
        repo = TradeRepository()
        stats = repo.get_statistics()
        logger.info(f"✅ Connection OK - Total trades: {stats['total_trades']}")
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize database')
    parser.add_argument('--drop', action='store_true', help='Drop existing tables')
    args = parser.parse_args()
    
    init_database(drop_existing=args.drop)
