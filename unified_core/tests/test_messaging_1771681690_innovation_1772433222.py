import pytest

class MockMessagingSystem:
    def send_message(self, message: str) -> None:
        print(f"Sending email: {message}")

@pytest.fixture
def messaging_system():
    return MockMessagingSystem()

def test_send_message_happy_path(messaging_system):
    # Arrange
    expected_message = "Hello, world!"
    
    # Act
    messaging_system.send_message(expected_message)
    
    # Assert (since the function prints directly, we capture stdout for verification)
    captured_output = capsys.readouterr()
    assert captured_output.out == f"Sending email: {expected_message}\n"

def test_send_message_edge_case_empty(messaging_system):
    # Arrange
    expected_message = ""
    
    # Act
    messaging_system.send_message(expected_message)
    
    # Assert (since the function prints directly, we capture stdout for verification)
    captured_output = capsys.readouterr()
    assert captured_output.out == f"Sending email: {expected_message}\n"

def test_send_message_edge_case_none(messaging_system):
    # Arrange
    expected_message = None
    
    # Act
    messaging_system.send_message(expected_message)
    
    # Assert (since the function prints directly, we capture stdout for verification)
    captured_output = capsys.readouterr()
    assert captured_output.out == f"Sending email: {expected_message}\n"

# There are no error cases to test in this code since it does not raise any exceptions