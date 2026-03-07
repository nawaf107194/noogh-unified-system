import pytest

from unified_core.lab_container_service import get_lab_service, LabContainerService

@pytest.fixture(autouse=True)
def reset_global_labservice():
    global _lab_service
    _lab_service = None

@pytest.mark.parametrize("input_data", [None, "", [], {}, 0])
def test_get_lab_service_with_invalid_input(input_data):
    result = get_lab_service()
    assert result is not None
    assert isinstance(result, LabContainerService)

def test_get_lab_service_happy_path():
    result1 = get_lab_service()
    result2 = get_lab_service()
    assert result1 is result2
    assert isinstance(result1, LabContainerService)