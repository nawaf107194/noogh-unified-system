import pytest

from unified_core.initialization import require_ready

class MockInitializationClass:
    _startup_complete = False

def test_require_ready_happy_path():
    # Set up a mock class instance with startup complete
    mock_instance = MockInitializationClass()
    mock_instance._startup_complete = True
    
    # Call the function, expect no exception
    assert require_ready(mock_instance) is None

def test_require_ready_error_case():
    # Set up a mock class instance without startup complete
    mock_instance = MockInitializationClass()
    
    # Call the function and expect it to raise a RuntimeError
    with pytest.raises(RuntimeError):
        require_ready(mock_instance)