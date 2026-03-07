import pytest
from unified_core.lab_container_service import LabContainerService, get_lab_service

@pytest.fixture(autouse=True)
def reset_lab_service():
    global _lab_service
    _lab_service = None

def test_get_lab_service_happy_path():
    """Test the happy path where the service is created and returned"""
    service1 = get_lab_service()
    service2 = get_lab_service()
    
    assert isinstance(service1, LabContainerService)
    assert id(service1) == id(service2)

def test_get_lab_service_first_call_creates_instance():
    """Test that calling `get_lab_service` for the first time creates an instance"""
    service = get_lab_service()
    assert service is not None
    assert isinstance(service, LabContainerService)

def test_get_lab_service_subsequent_calls_return_same_instance():
    """Test that subsequent calls return the same instance"""
    service1 = get_lab_service()
    service2 = get_lab_service()
    
    assert id(service1) == id(service2)