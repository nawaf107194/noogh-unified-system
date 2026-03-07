import pytest

from unified_core.lab_container_service import LabContainerService, get_lab_service

@pytest.fixture(autouse=True)
def reset_global_service():
    """Reset the global _lab_service before each test"""
    global _lab_service
    _lab_service = None
    yield
    _lab_service = None

class TestGetLabService:

    def test_happy_path(self):
        # Call the function and get the result
        result = get_lab_service()
        
        # Assert that the result is an instance of LabContainerService
        assert isinstance(result, LabContainerService)
        # Ensure the global variable _lab_service was set
        assert globals()['_lab_service'] is not None

    def test_edge_case_none(self):
        # Call the function and get the result
        result = get_lab_service()
        
        # Reset the global variable to mimic an edge case where it might be None unexpectedly
        global _lab_service
        _lab_service = None
        
        # Call the function again and get the result
        result = get_lab_service()
        
        # Assert that the result is an instance of LabContainerService
        assert isinstance(result, LabContainerService)
        # Ensure the global variable _lab_service was set
        assert globals()['_lab_service'] is not None

    def test_error_case_invalid_input(self):
        """This function does not explicitly raise exceptions for invalid inputs, so we skip this test"""
        pass

    @pytest.mark.asyncio
    async def test_async_behavior(self):
        # This function does not involve any async behavior, so we skip this test
        pass