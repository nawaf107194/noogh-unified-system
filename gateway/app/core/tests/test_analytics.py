import pytest
import sqlite3

class Analytics:
    def __init__(self, db_path):
        self.db_path = db_path

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS job_metrics (
                    id TEXT PRIMARY KEY,
                    job_type TEXT,
                    steps INTEGER,
                    duration_ms REAL,
                    status TEXT,
                    timestamp DATETIME
                )
            """
            )

def test_init_db_happy_path(tmpdir):
    db_path = str(tmpdir.join("test.db"))
    analytics = Analytics(db_path)
    analytics._init_db()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='job_metrics'")
    table_exists = cursor.fetchone() is not None
    assert table_exists

def test_init_db_edge_case_empty_db_path():
    with pytest.raises(TypeError):
        Analytics(None)._init_db()

def test_init_db_error_case_invalid_db_path(tmpdir):
    invalid_path = str(tmpdir.join("invalid.db"))
    analytics = Analytics(invalid_path)
    with pytest.raises(sqlite3.Error):
        analytics._init_db()