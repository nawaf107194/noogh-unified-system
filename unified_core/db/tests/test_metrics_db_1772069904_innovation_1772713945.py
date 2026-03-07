import pytest
from unittest.mock import Mock
from src.unified_core.db.metrics_db_1772069904 import MetricsDB
from src.unified_core.db.data_router import DataRouter
from src.unified_core.db.postgres_manager import PostgresManager

def test_metricsdb_init_happy_path():
    """Test MetricsDB initialization with valid config"""
    db_config = {
        "host": "localhost",
        "port": 5432,
        "dbname": "test_db",
        "user": "test_user",
        "password": "test_pass"
    }
    
    metrics_db = MetricsDB(db_config)
    
    assert isinstance(metrics_db.db_router, DataRouter)
    assert isinstance(metrics_db.pg_manager, PostgresManager)
    assert metrics_db.pg_manager.config == db_config

def test_metricsdb_init_empty_config():
    """Test MetricsDB initialization with empty config"""
    db_config = {}
    with pytest.raises(KeyError):
        MetricsDB(db_config)

def test_metricsdb_init_none_config():
    """Test MetricsDB initialization with None config"""
    db_config = None
    with pytest.raises(TypeError):
        MetricsDB(db_config)