import pytest
from unittest.mock import patch
import os
import time
from dataclasses import asdict
from cognitive_journal import JournalEntry

@pytest.fixture
def journal_entry():
    return JournalEntry(
        timestamp=time.time(),
        content="Test entry",
        tags=["test", "example"]
    )

@pytest.fixture
def journal_instance(tmpdir):
    with patch('os.path.exists', return_value=True):
        return CognitiveJournal(directory=tmpdir)

def test_save_entry_happy_path(journal_instance, journal_entry, tmpdir):
    # Arrange
    expected_file = os.path.join(str(tmpdir), f"journal_{time.strftime('%Y-%m-%d', time.localtime(journal_entry.timestamp))}.jsonl")
    
    # Act
    journal_instance._save_entry(journal_entry)
    
    # Assert
    assert os.path.exists(expected_file)
    with open(expected_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        saved_entry = json.loads(lines[0])
        assert saved_entry == asdict(journal_entry)

def test_save_entry_empty_entry(journal_instance):
    # Arrange
    entry = JournalEntry(timestamp=time.time(), content="", tags=[])
    
    # Act & Assert
    journal_instance._save_entry(entry)
    # If the function doesn't raise an exception, it's considered a success

def test_save_entry_none_entry(journal_instance):
    # Arrange
    entry = None
    
    # Act & Assert
    journal_instance._save_entry(entry)
    # If the function doesn't raise an exception, it's considered a success

def test_save_entry_invalid_input(journal_instance):
    # Arrange
    entry = "not_a_JournalEntry"
    
    # Act & Assert
    journal_instance._save_entry(entry)
    # If the function doesn't raise an exception, it's considered a success

def test_logger_error_on_failure(mocker, journal_instance, journal_entry):
    # Arrange
    with patch('cognitive_journal.logger.error') as mock_error:
        with patch('builtins.open', side_effect=IOError("Test error")):
            # Act
            journal_instance._save_entry(journal_entry)
            
            # Assert
            mock_error.assert_called_once_with("📓 Failed to save entry: Test error")