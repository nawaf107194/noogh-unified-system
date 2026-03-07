import pytest

from unified_core.db.postgres import PostgresDB, Pool

class TestPostgresDBInit:
    def test_happy_path(self):
        db = PostgresDB(
            host="localhost",
            port=5432,
            database="unified_core",
            user="postgres",
            password="password",
            min_connections=5,
            max_connections=20,
            command_timeout=60.0
        )
        assert db.dsn == "postgresql://postgres:password@localhost:5432/unified_core"
        assert db.min_connections == 5
        assert db.max_connections == 20
        assert db.command_timeout == 60.0
        assert db._pool is None
        assert not db._initialized

    def test_empty_values(self):
        with pytest.raises(ValueError) as exc_info:
            PostgresDB(
                host="",
                port=5432,
                database="unified_core",
                user="postgres",
                password="password",
                min_connections=5,
                max_connections=20,
                command_timeout=60.0
            )
        assert str(exc_info.value) == "host cannot be empty"

    def test_none_values(self):
        with pytest.raises(ValueError) as exc_info:
            PostgresDB(
                host=None,
                port=5432,
                database="unified_core",
                user="postgres",
                password="password",
                min_connections=5,
                max_connections=20,
                command_timeout=60.0
            )
        assert str(exc_info.value) == "host cannot be None"

    def test_invalid_port(self):
        with pytest.raises(ValueError) as exc_info:
            PostgresDB(
                host="localhost",
                port=-1,
                database="unified_core",
                user="postgres",
                password="password",
                min_connections=5,
                max_connections=20,
                command_timeout=60.0
            )
        assert str(exc_info.value) == "port must be a positive integer"

    def test_min_max_connections(self):
        with pytest.raises(ValueError) as exc_info:
            PostgresDB(
                host="localhost",
                port=5432,
                database="unified_core",
                user="postgres",
                password="password",
                min_connections=10,
                max_connections=5,
                command_timeout=60.0
            )
        assert str(exc_info.value) == "min_connections must be less than or equal to max_connections"

    def test_negative_command_timeout(self):
        with pytest.raises(ValueError) as exc_info:
            PostgresDB(
                host="localhost",
                port=5432,
                database="unified_core",
                user="postgres",
                password="password",
                min_connections=5,
                max_connections=20,
                command_timeout=-1.0
            )
        assert str(exc_info.value) == "command_timeout must be a positive number"

    def test_non_int_min_max_connections(self):
        with pytest.raises(ValueError) as exc_info:
            PostgresDB(
                host="localhost",
                port=5432,
                database="unified_core",
                user="postgres",
                password="password",
                min_connections=5.0,
                max_connections=20,
                command_timeout=60.0
            )
        assert str(exc_info.value) == "min_connections and max_connections must be integers"

    def test_non_float_command_timeout(self):
        with pytest.raises(ValueError) as exc_info:
            PostgresDB(
                host="localhost",
                port=5432,
                database="unified_core",
                user="postgres",
                password="password",
                min_connections=5,
                max_connections=20,
                command_timeout="60.0"
            )
        assert str(exc_info.value) == "command_timeout must be a float"

    def test_async_behavior(self, monkeypatch):
        async def mock_create_engine(*args, **kwargs):
            return Pool()

        from sqlalchemy.ext.asyncio import create_async_engine

        monkeypatch.setattr(create_async_engine, 'from_url', mock_create_engine)

        db = PostgresDB(
            host="localhost",
            port=5432,
            database="unified_core",
            user="postgres",
            password="password",
            min_connections=5,
            max_connections=20,
            command_timeout=60.0
        )

        assert isinstance(db._pool, Pool)
        assert db._initialized