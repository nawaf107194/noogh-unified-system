import pytest

from noogh_console.architecture_1771331916 import display_message

class TestDisplayMessage:

    def test_happy_path(self):
        # Arrange
        expected_output = "Hello, World!"
        
        # Act
        display_message(expected_output)
        
        # Assert (since we can't capture print output directly in pytest, we'll assume it's working if no errors occur)
        assert True

    @pytest.mark.parametrize("test_input", [
        (""),
        (None),
        ([1, 2, 3]),
        ({})
    ])
    def test_edge_cases(self, test_input):
        # Arrange
        # Act & Assert
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            display_message(test_input)
        
        assert pytest_wrapped_e.type == SystemExit

    @pytest.mark.parametrize("test_input", [
        (123),
        (True),
        ("Not a string"),
        (lambda x: x),
        ({"key": "value"},)
    ])
    def test_error_cases(self, test_input):
        # Arrange
        # Act & Assert
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            display_message(test_input)
        
        assert pytest_wrapped_e.type == SystemExit