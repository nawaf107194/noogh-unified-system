import pytest
from datetime import datetime
from monitor_agent import print_header

def test_print_header_happy_path(capsys):
    """Test the happy path where the function prints the header correctly."""
    print_header()
    captured = capsys.readouterr()
    expected = (
        "=" * 80 + "\n"
        "🤖 NOOGH AGENT MONITORING DASHBOARD | لوحة مراقبة وكيل نوغ".center(80) + "\n"
        "=" * 80 + "\n"
        f"⏰ Time | الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        "=" * 80
    )
    assert captured.out.strip() == expected

def test_print_header_edge_case_empty_string(capsys):
    """Test the edge case where an empty string is passed."""
    with pytest.raises(ValueError) as e:
        print_header("")
    assert str(e.value) == "Invalid input: Expected a non-empty string"

def test_print_header_edge_case_none(capsys):
    """Test the edge case where None is passed."""
    with pytest.raises(ValueError) as e:
        print_header(None)
    assert str(e.value) == "Invalid input: Expected a non-empty string"

def test_print_header_error_case_invalid_input(capsys):
    """Test the error case where an invalid input type is passed."""
    with pytest.raises(TypeError) as e:
        print_header(123)
    assert str(e.value) == "Invalid input: Expected a non-empty string"

# Assuming the datetime.now() can be mocked, we can test it with a fixed value
from unittest.mock import patch

@patch('monitor_agent.datetime')
def test_print_header_async_behavior(mock_datetime, capsys):
    """Test async behavior by mocking the current time."""
    mock_datetime.now.return_value = datetime(2023, 10, 10, 12, 0, 0)
    
    print_header()
    captured = capsys.readouterr()
    expected = (
        "=" * 80 + "\n"
        "🤖 NOOGH AGENT MONITORING DASHBOARD | لوحة مراقبة وكيل نوغ".center(80) + "\n"
        "=" * 80 + "\n"
        f"⏰ Time | الوقت: {datetime(2023, 10, 10, 12, 0, 0).strftime('%Y-%m-%d %H:%M:%S')}\n"
        "=" * 80
    )
    assert captured.out.strip() == expected