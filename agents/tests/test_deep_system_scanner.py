import pytest
from unittest.mock import patch, MagicMock
import sqlite3
import time
import json

from agents.deep_system_scanner import _inject, DB_PATH

def test_inject_happy_path():
    key = "test_key"
    data = {"value": 42}
    label = "happy_test"

    with patch('sqlite3.connect') as mock_connect:
        conn_mock = MagicMock()
        cur_mock = MagicMock()
        conn_mock.cursor.return_value = cur_mock
        mock_connect.return_value = conn_mock

        _inject(key, data, label)

        cur_mock.execute.assert_called_once_with(
            "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) VALUES (?,?,?,?)",
            (key, json.dumps(data, ensure_ascii=False, default=str), 0.95, time.time())
        )
        conn_mock.commit.assert_called_once()
        conn_mock.close.assert_called_once()
        print.assert_called_with("  ✅ حُقن: happy_test")

def test_inject_edge_case_empty_key():
    key = ""
    data = {"value": 42}
    label = "empty_key"

    with patch('sqlite3.connect') as mock_connect:
        _inject(key, data, label)

        print.assert_called_with(f"  ⚠️  فشل حقن {label}: sqlite3.IntegrityError: UNIQUE constraint failed")

def test_inject_edge_case_none_data():
    key = "test_key"
    data = None
    label = "none_data"

    with patch('sqlite3.connect') as mock_connect:
        _inject(key, data, label)

        print.assert_called_with(f"  ⚠️  فشل حقن {label}: sqlite3.IntegrityError: UNIQUE constraint failed")

def test_inject_edge_case_boundary_value():
    key = "test_key"
    data = {"value": float('inf')}
    label = "boundary_value"

    with patch('sqlite3.connect') as mock_connect:
        _inject(key, data, label)

        print.assert_called_with(f"  ⚠️  فشل حقن {label}: sqlite3.IntegrityError: UNIQUE constraint failed")

def test_inject_error_case_invalid_input():
    key = "test_key"
    data = {"value": object()}
    label = "invalid_input"

    with patch('sqlite3.connect') as mock_connect:
        _inject(key, data, label)

        print.assert_called_with(f"  ⚠️  فشل حقن {label}: sqlite3.IntegrityError: UNIQUE constraint failed")