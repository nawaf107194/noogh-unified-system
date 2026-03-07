import pytest

from unified_core.db.postgres import Postgres

def test_init_happy_path():
    db = Postgres(
        host="localhost",
        port=5432,
        database="unified_core",
        user="postgres",
        password="",
        min_connections=5,
        max_connections=20,
        command_timeout=60.0
    )
    assert isinstance(db, Postgres)
    assert db.dsn == "postgresql://postgres:@localhost:5432/unified_core"
    assert db.min_connections == 5
    assert db.max_connections == 20
    assert db.command_timeout == 60.0
    assert db._pool is None
    assert not db._initialized

def test_init_edge_case_empty_host():
    with pytest.raises(ValueError):
        Postgres(
            host="",
            port=5432,
            database="unified_core",
            user="postgres",
            password="",
            min_connections=5,
            max_connections=20,
            command_timeout=60.0
        )

def test_init_edge_case_none_database():
    with pytest.raises(ValueError):
        Postgres(
            host="localhost",
            port=5432,
            database=None,
            user="postgres",
            password="",
            min_connections=5,
            max_connections=20,
            command_timeout=60.0
        )

def test_init_edge_case_min_max_bounds():
    db = Postgres(
        host="localhost",
        port=5432,
        database="unified_core",
        user="postgres",
        password="",
        min_connections=1,
        max_connections=200,
        command_timeout=60.0
    )
    assert db.min_connections == 1
    assert db.max_connections == 200

def test_init_error_case_invalid_min_max():
    with pytest.raises(ValueError):
        Postgres(
            host="localhost",
            port=5432,
            database="unified_core",
            user="postgres",
            password="",
            min_connections=10,
            max_connections=5,
            command_timeout=60.0
        )

def test_init_error_case_negative_min_connections():
    with pytest.raises(ValueError):
        Postgres(
            host="localhost",
            port=5432,
            database="unified_core",
            user="postgres",
            password="",
            min_connections=-1,
            max_connections=20,
            command_timeout=60.0
        )

def test_init_error_case_zero_max_connections():
    with pytest.raises(ValueError):
        Postgres(
            host="localhost",
            port=5432,
            database="unified_core",
            user="postgres",
            password="",
            min_connections=1,
            max_connections=0,
            command_timeout=60.0
        )