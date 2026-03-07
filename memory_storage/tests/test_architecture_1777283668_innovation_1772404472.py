import pytest

def handle_error(e):
    """Utility function to handle errors consistently."""
    print(f"An error occurred: {str(e)}")

def test_handle_error_happy_path():
    # Happy path - normal input
    handle_error("Invalid input")
    assert True  # No specific assertion needed, just ensure it doesn't raise an exception

def test_handle_error_edge_cases_empty_input():
    # Edge case - empty string input
    handle_error("")
    assert True  # No specific assertion needed, just ensure it doesn't raise an exception

def test_handle_error_edge_cases_none_input():
    # Edge case - None input
    handle_error(None)
    assert True  # No specific assertion needed, just ensure it doesn't raise an exception

# Note: There are no error cases in the provided code as it only prints the error message.
# If there were error handling logic (like raising exceptions), we would add tests for those.

# Asynchronous behavior is not applicable here as the function is synchronous and does not involve any async operations.