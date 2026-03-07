import pytest

class MockDBConnection:
    def __init__(self):
        self.cursor = None

    def cursor(self):
        if not self.cursor:
            self.cursor = MockCursor()
        return self.cursor

    def commit(self):
        pass  # No-op for this mock, as we're only interested in the execute call

class MockCursor:
    def __init__(self):
        self.executed_query = None
        self.executed_args = None

    def execute(self, query, args):
        self.executed_query = query
        self.executed_args = args

class ConfigManager:
    def __init__(self):
        self.db_connection = MockDBConnection()

    def save(self, data):
        cursor = self.db_connection.cursor()
        cursor.execute("UPDATE settings SET config = %s", (data,))
        self.db_connection.commit()

# Happy path
def test_save_happy_path():
    config_manager = ConfigManager()
    data = {"key": "value"}
    config_manager.save(data)
    assert config_manager.db_connection.cursor.executed_query == "UPDATE settings SET config = %s"
    assert config_manager.db_connection.cursor.executed_args == (data,)

# Edge cases
def test_save_empty_data():
    config_manager = ConfigManager()
    data = {}
    config_manager.save(data)
    assert config_manager.db_connection.cursor.executed_query == "UPDATE settings SET config = %s"
    assert config_manager.db_connection.cursor.executed_args == (data,)

def test_save_none_data():
    config_manager = ConfigManager()
    data = None
    config_manager.save(data)
    assert config_manager.db_connection.cursor.executed_query == "UPDATE settings SET config = %s"
    assert config_manager.db_connection.cursor.executed_args == (data,)

# Error cases - No exceptions are explicitly raised in the code, so these tests are hypothetical
def test_save_invalid_data_type():
    # This is a hypothetical scenario since no exception is raised for invalid data types
    pass

def test_save_database_error():
    # This is a hypothetical scenario since no exception is raised for database errors
    pass

# Async behavior - The function does not appear to be asynchronous, so this is not applicable