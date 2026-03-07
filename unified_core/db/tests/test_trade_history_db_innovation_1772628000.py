import pytest
from unittest.mock import Mock
from unified_core.db.trade_history_db import TradeHistoryDB
from unified_core.router.data_router import DataRouter

def test_init_happy_path():
    """Test that TradeHistoryDB initializes correctly with valid DataRouter"""
    mock_router = Mock(spec=DataRouter)
    th_db = TradeHistoryDB(mock_router)
    assert th_db.router == mock_router

def test_init_with_none():
    """Test that TradeHistoryDB initializes with None router"""
    th_db = TradeHistoryDB(None)
    assert th_db.router is None