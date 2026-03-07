import pytest

class MockDAL:
    def execute_query(self, query, params):
        if query == "SELECT * FROM users":
            return [{"id": 1, "name": "John"}]
        elif query is None or params is None:
            return None
        else:
            raise Exception("Unexpected query or params")

class TestDashboardApp:
    def test_fetch_data_happy_path(self):
        # Arrange
        dashboard = Dashboard(dal=MockDAL())
        
        # Act
        result = dashboard.fetch_data("SELECT * FROM users")
        
        # Assert
        assert result == [{"id": 1, "name": "John"}]

    def test_fetch_data_empty_query(self):
        # Arrange
        dashboard = Dashboard(dal=MockDAL())
        
        # Act
        result = dashboard.fetch_data("")
        
        # Assert
        assert result is None

    def test_fetch_data_none_query_and_params(self):
        # Arrange
        dashboard = Dashboard(dal=MockDAL())
        
        # Act
        result = dashboard.fetch_data(None, params=None)
        
        # Assert
        assert result is None

    def test_fetch_data_invalid_query(self):
        # Arrange
        dashboard = Dashboard(dal=MockDAL())
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            dashboard.fetch_data("SELECT * FROM invalid_table")
        assert str(exc_info.value) == "Unexpected query or params"