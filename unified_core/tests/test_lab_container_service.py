import pytest
from unittest.mock import patch, MagicMock
from unified_core.lab_container_service import LabContainerService, get_lab_service

class TestLabContainerService:

    @pytest.fixture(autouse=True)
    def setup(self):
        global _lab_service
        _lab_service = None  # Reset the global variable before each test

    def test_happy_path(self):
        # Test the happy path where the service is created and returned
        service = get_lab_service()
        assert isinstance(service, LabContainerService)

    def test_edge_case_none(self):
        # Test the edge case where the global variable is explicitly set to None
        global _lab_service
        _lab_service = None
        service = get_lab_service()
        assert isinstance(service, LabContainerService)

    def test_async_behavior(self):
        # Since the function is not asynchronous, we can't really test async behavior.
        # However, we can mock the global variable to ensure it's only created once.
        with patch('unified_core.lab_container_service._lab_service', None):
            service1 = get_lab_service()
            service2 = get_lab_service()
            assert service1 is service2

    def test_error_case_invalid_input(self):
        # The function does not take any input arguments, so there's no invalid input scenario.
        # This test is more about ensuring the function behaves as expected without any arguments.
        with pytest.raises(TypeError) as excinfo:
            get_lab_service("invalid_arg")
        assert "get_lab_service() takes 0 positional arguments but 1 was given" in str(excinfo.value)

    def test_global_service_creation(self):
        # Ensure the global service is only created once
        with patch('unified_core.lab_container_service.LabContainerService') as MockService:
            instance = MockService.return_value
            service1 = get_lab_service()
            service2 = get_lab_service()
            assert service1 is instance
            assert service2 is instance
            MockService.assert_called_once()

    def test_global_service_reset(self):
        # Test that resetting the global service results in a new instance
        service1 = get_lab_service()
        global _lab_service
        _lab_service = None
        service2 = get_lab_service()
        assert service1 is not service2