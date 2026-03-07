import pytest

def handle_error(e):
    """Utility function to handle errors consistently."""
    print(f"An error occurred: {str(e)}")

class TestHandleError:

    def test_happy_path(self):
        # Arrange
        error_message = "Something went wrong"
        
        # Act
        result = handle_error(error_message)
        
        # Assert
        assert result is None  # No return value, so expect None
        
    def test_edge_case_empty_string(self):
        # Arrange
        error_message = ""
        
        # Act
        result = handle_error(error_message)
        
        # Assert
        assert result is None  # No return value, so expect None
        
    def test_edge_case_none(self):
        # Arrange
        error_message = None
        
        # Act
        result = handle_error(error_message)
        
        # Assert
        assert result is None  # No return value, so expect None

# Note: There are no explicit error cases in the function. It only accepts a single argument and always returns None.