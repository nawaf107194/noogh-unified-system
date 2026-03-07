import pytest
from sqlalchemy.exc import ArgumentError
from unified_core.intelligence.temporal_reasoning import TemporalReasoning

def test_temporal_reasoning_init_valid_connection():
    """Test that the engine is created successfully with a valid connection string"""
    db_connection_str = 'sqlite:///:memory:'
    tr = TemporalReasoning(db_connection_str)
    assert tr.engine is not None

def test_temporal_reasoning_init_empty_string():
    """Test that empty string connection raises exception"""
    db_connection_str = ''
    with pytest.raises(ArgumentError):
        TemporalReasoning(db_connection_str)

def test_temporal_reasoning_init_none():
    """Test that None connection raises exception"""
    db_connection_str = None
    with pytest.raises(ArgumentError):
        TemporalReasoning(db_connection_str)

def test_temporal_reasoning_init_invalid_connection():
    """Test that invalid connection string raises exception"""
    db_connection_str = 'invalid_connection'
    with pytest.raises(ArgumentError):
        TemporalReasoning(db_connection_str)