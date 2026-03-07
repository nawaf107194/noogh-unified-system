import pytest

class MockDBConnection:
    def execute(self, query):
        if query == "SELECT * FROM users":
            return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        else:
            raise Exception("Query not supported")

@pytest.fixture
def db_connection():
    return MockDBConnection()

class SystemUnderTest:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def query_data(self, query):
        return self.db_connection.execute(query)

def test_query_data_happy_path(db_connection):
    system_under_test = SystemUnderTest(db_connection)
    result = system_under_test.query_data("SELECT * FROM users")
    assert result == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

def test_query_data_empty_query(db_connection):
    system_under_test = SystemUnderTest(db_connection)
    result = system_under_test.query_data("")
    assert result is None

def test_query_data_none_query(db_connection):
    system_under_test = SystemUnderTest(db_connection)
    result = system_under_test.query_data(None)
    assert result is None

def test_query_data_boundary_case(db_connection):
    system_under_test = SystemUnderTest(db_connection)
    result = system_under_test.query_data("SELECT * FROM users LIMIT 1")
    assert result == [{"id": 1, "name": "Alice"}]

def test_query_data_invalid_query_no_exception_raised(db_connection):
    system_under_test = SystemUnderTest(db_connection)
    result = system_under_test.query_data("INVALID QUERY")
    assert result is None