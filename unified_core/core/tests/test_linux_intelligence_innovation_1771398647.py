import pytest

class MockLinuxIntelligence:
    def __init__(self, active: str, sub_state: str):
        self.active = active
        self.sub_state = sub_state

@pytest.fixture
def healthy_instance():
    return MockLinuxIntelligence(active="active", sub_state="running")

@pytest.fixture
def unhealthy_instance():
    return MockLinuxIntelligence(active="inactive", sub_state="stopped")

@pytest.fixture
def partially_healthy_instance():
    return MockLinuxIntelligence(active="active", sub_state="stopped")

def test_is_healthy_happy_path(healthy_instance):
    assert healthy_instance.is_healthy() == True

def test_is_healthy_unhappy_path(unhealthy_instance):
    assert unhealthy_instance.is_healthy() == False

def test_is_healthy_partial_match(partially_healthy_instance):
    assert partially_healthy_instance.is_healthy() == False

def test_is_healthy_edge_case_empty_strings():
    instance = MockLinuxIntelligence(active="", sub_state="")
    assert instance.is_healthy() == False

def test_is_healthy_edge_case_none_values():
    instance = MockLinuxIntelligence(active=None, sub_state=None)
    assert instance.is_healthy() == False

def test_is_healthy_error_case_invalid_inputs():
    instance = MockLinuxIntelligence(active=123, sub_state=True)
    with pytest.raises(AttributeError):
        instance.is_healthy()

# Since the function does not involve any async operations, there's no need to test async behavior.