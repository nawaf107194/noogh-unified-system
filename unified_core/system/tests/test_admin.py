import pytest

from unified_core.system.admin import Admin

class TestAdminInit:

    def test_happy_path(self):
        # Arrange
        expected_data_router = DataRouter()

        # Act
        admin = Admin()
        actual_data_router = admin.data_router

        # Assert
        assert actual_data_router == expected_data_router, "The data_router should be an instance of DataRouter"

    def test_edge_case_none_input(self):
        with pytest.raises(TypeError) as excinfo:
            admin = Admin(None)
        
        assert str(excinfo.value) == "Admin does not accept any parameters", "Should raise TypeError when None is passed"

    def test_error_cases_invalid_input(self):
        # Assuming DataRouter has a constructor that raises an error for invalid input
        with pytest.raises(ValueError) as excinfo:
            admin = Admin("invalid_input")
        
        assert str(excinfo.value) == "Invalid input for DataRouter", "Should raise ValueError when invalid input is passed"

    def test_async_behavior(self):
        # Assuming DataRouter has an asynchronous method that needs to be tested
        async def check_data_router():
            await asyncio.sleep(0.1)
            return DataRouter()

        data_router = asyncio.run(check_data_router())
        
        admin = Admin()
        actual_data_router = admin.data_router

        assert actual_data_router == data_router, "The data_router should match the asynchronously created DataRouter instance"