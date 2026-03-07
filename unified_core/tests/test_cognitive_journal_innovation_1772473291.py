import pytest
from unittest.mock import patch, mock_open
from datetime import datetime
import os
import json
from collections import namedtuple

JournalEntry = namedtuple('JournalEntry', ['timestamp', 'content'])
logger = mock.Mock()

class CognitiveJournal:
    def __init__(self, dir):
        self._dir = dir

    def _save_entry(self, entry: JournalEntry):
        """Save a single entry to disk."""
        try:
            # Daily file rotation
            day_str = time.strftime("%Y-%m-%d", time.localtime(entry.timestamp))
            filepath = os.path.join(self._dir, f"journal_{day_str}.jsonl")
            
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"📓 Failed to save entry: {e}")

# Tests
@pytest.fixture
def cognitive_journal(tmpdir):
    return CognitiveJournal(tmpdir.strpath)

def test_save_entry_happy_path(cognitive_journal, tmpdir):
    # Setup
    day_str = datetime.now().strftime("%Y-%m-%d")
    expected_file = os.path.join(tmpdir.strpath, f"journal_{day_str}.jsonl")
    
    entry = JournalEntry(timestamp=datetime.now().timestamp(), content="Test Entry")
    
    # Execute
    cognitive_journal._save_entry(entry)
    
    # Verify
    assert os.path.exists(expected_file)
    with open(expected_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) == 1
        assert json.loads(lines[0]) == asdict(entry)

def test_save_entry_edge_case_empty_content(cognitive_journal):
    # Setup
    entry = JournalEntry(timestamp=datetime.now().timestamp(), content="")
    
    # Execute
    cognitive_journal._save_entry(entry)
    
    # Verify
    logger.error.assert_called_once_with("📓 Failed to save entry: empty content")

def test_save_entry_edge_case_none_timestamp(cognitive_journal, tmpdir):
    # Setup
    expected_file = os.path.join(tmpdir.strpath, "journal_0001-01-01.jsonl")
    
    entry = JournalEntry(timestamp=None, content="Test Entry")
    
    with patch('time.strftime', return_value="2023-01-01"):
        cognitive_journal._save_entry(entry)
        
    # Verify
    assert os.path.exists(expected_file)
    with open(expected_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) == 1
        assert json.loads(lines[0]) == {'timestamp': None, 'content': "Test Entry"}

def test_save_entry_error_case_invalid_timestamp(cognitive_journal):
    # Setup
    entry = JournalEntry(timestamp=123456789, content="Test Entry")
    
    # Execute and Verify
    with patch('time.strftime', side_effect=TypeError("Invalid timestamp")):
        cognitive_journal._save_entry(entry)
        
    logger.error.assert_called_once_with("📓 Failed to save entry: Invalid timestamp")