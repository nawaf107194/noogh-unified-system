import pytest
from agents.deep_system_scanner import _inject
import sqlite3
import json
import time

DB_PATH = 'test_db.db'

def setup_module():
    # Setup test database
    conn = sqlite3.connect(DB_PATH, timeout=8)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS beliefs (key TEXT PRIMARY KEY, value TEXT, utility_score REAL, updated_at REAL)")
    conn.commit(); conn.close()

def teardown_module():
    # Cleanup test database
    conn = sqlite3.connect(DB_PATH, timeout=8)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS beliefs")
    conn.commit(); conn.close()

def test_happy_path():
    key = "test_key"
    data = {"value": 123}
    label = "test_label"
    
    _inject(key, data, label)
    
    # Check if the record was inserted correctly
    conn = sqlite3.connect(DB_PATH, timeout=8)
    cur = conn.cursor()
    cur.execute("SELECT * FROM beliefs WHERE key = ?", (key,))
    result = cur.fetchone()
    conn.close()
    
    assert result is not None
    assert result[0] == key
    assert json.loads(result[1]) == data
    assert result[2] == 0.95
    assert abs(time.time() - result[3]) < 1

def test_edge_case_empty_data():
    key = "test_key"
    data = {}
    label = "empty_data_label"
    
    _inject(key, data, label)
    
    conn = sqlite3.connect(DB_PATH, timeout=8)
    cur = conn.cursor()
    cur.execute("SELECT * FROM beliefs WHERE key = ?", (key,))
    result = cur.fetchone()
    conn.close()
    
    assert result is not None
    assert result[0] == key
    assert json.loads(result[1]) == data
    assert result[2] == 0.95
    assert abs(time.time() - result[3]) < 1

def test_edge_case_none_data():
    key = "test_key"
    data = None
    label = "none_data_label"
    
    _inject(key, data, label)
    
    conn = sqlite3.connect(DB_PATH, timeout=8)
    cur = conn.cursor()
    cur.execute("SELECT * FROM beliefs WHERE key = ?", (key,))
    result = cur.fetchone()
    conn.close()
    
    assert result is not None
    assert result[0] == key
    assert json.loads(result[1]) == {}
    assert result[2] == 0.95
    assert abs(time.time() - result[3]) < 1

def test_error_case_invalid_key_type():
    with pytest.raises(TypeError):
        _inject(None, {"value": 123}, "invalid_key_type_label")

def test_error_case_invalid_data_type():
    with pytest.raises(TypeError):
        _inject("test_key", None, "invalid_data_type_label")