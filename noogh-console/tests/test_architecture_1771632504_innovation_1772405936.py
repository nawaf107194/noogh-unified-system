import pytest

class TestDatabaseOperations:
    @pytest.fixture
    def mock_database_operations(self):
        class MockDatabaseOperations:
            pass
        return MockDatabaseOperations()

    def test_happy_path(self, mock_database_operations):
        subject = __init__(mock_database_operations)
        assert subject.database_operations is mock_database_operations

    def test_edge_case_none(self):
        with pytest.raises(TypeError) as excinfo:
            subject = __init__(None)
        assert str(excinfo.value) == "database_operations must not be None"

    def test_error_case_invalid_type(self, mock_database_operations):
        with pytest.raises(TypeError) as excinfo:
            subject = __init__("not a database operations instance")
        assert str(excinfo.value) == "database_operations must be an instance of DatabaseOperations"