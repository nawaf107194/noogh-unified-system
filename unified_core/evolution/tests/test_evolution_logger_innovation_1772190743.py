import pytest

from unified_core.evolution.evolution_logger import clear_request_id, _context

@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test to ensure clean state."""
    _context.request_id = "some_request_id"  # Set an initial request ID for testing
    yield
    _context.request_id = None  # Reset the request ID back to None after tests

def test_clear_request_id_happy_path():
    """Test happy path with normal inputs."""
    clear_request_id()
    assert _context.request_id is None, "Request ID should be cleared"

def test_clear_request_id_edge_case_none():
    """Test edge case where the current request ID is already None."""
    _context.request_id = None
    clear_request_id()
    assert _context.request_id is None, "Request ID should remain None"

def test_clear_request_id_error_case_invalid_input():
    """Test error case with invalid inputs. This function does not raise exceptions explicitly."""
    pass  # No need to test for exceptions as the function does not raise them

# Async behavior is not applicable for this synchronous function