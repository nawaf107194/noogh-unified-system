import pytest
import os
from unittest.mock import patch, MagicMock
import json

class MockJournalEntry:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

@pytest.fixture
def cognitive_journal(tmp_path):
    class MockCognitiveJournal:
        def __init__(self, dir, max_memory=10):
            self._dir = dir
            self.max_memory = max_memory
            self._entries = []

        def _load(self):
            super()._load()

        def get_entries(self):
            return self._entries

    journal_dir = tmp_path / "journal"
    journal_dir.mkdir()
    return MockCognitiveJournal(dir=str(journal_dir))

@pytest.fixture
def mock_jsonl_files(tmp_path, cognitive_journal):
    file_paths = []
    for i in range(10):
        file_path = tmp_path / f"entries_{i}.jsonl"
        with open(file_path, "w", encoding="utf-8") as f:
            for j in range(5):
                entry_data = {
                    "timestamp": f"2023-04-{i+1}-T{j:02d}:00:00Z",
                    "content": f"Entry {j}"
                }
                json.dump(entry_data, f)
                f.write("\n")
        file_paths.append(str(file_path))
    return file_paths

def test_load_happy_path(cognitive_journal, mock_jsonl_files):
    cognitive_journal._dir = os.path.dirname(mock_jsonl_files[0])
    cognitive_journal._load()
    entries = cognitive_journal.get_entries()
    assert len(entries) == 35
    assert entries[-1].timestamp == "2023-04-10-T04:00:00Z"

def test_load_empty_directory(cognitive_journal):
    cognitive_journal._dir = os.path.join(os.getcwd(), "non_existent_dir")
    cognitive_journal._load()
    assert not cognitive_journal.get_entries()

def test_load_no_jsonl_files(cognitive_journal, tmp_path):
    cognitive_journal._dir = str(tmp_path)
    cognitive_journal._load()
    assert not cognitive_journal.get_entries()

def test_load_recent_files_only(cognitive_journal, mock_jsonl_files):
    cognitive_journal._dir = os.path.dirname(mock_jsonl_files[0])
    cognitive_journal._max_memory = 10
    cognitive_journal._load()
    entries = cognitive_journal.get_entries()
    assert len(entries) == 35
    assert entries[-1].timestamp == "2023-04-10-T04:00:00Z"

def test_load_invalid_json(cognitive_journal, tmp_path):
    file_path = tmp_path / "invalid.jsonl"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("This is not valid JSON\n")
    cognitive_journal._dir = str(tmp_path)
    cognitive_journal._load()
    assert len(cognitive_journal.get_entries()) == 0

def test_load_file_open_failure(mocker, cognitive_journal, tmp_path):
    mocker.patch('builtins.open', side_effect=IOError("File not found"))
    cognitive_journal._dir = str(tmp_path / "non_existent_file.jsonl")
    cognitive_journal._load()
    assert not cognitive_journal.get_entries()

def test_load_entry_parsing_failure(cognitive_journal, tmp_path, mock_jsonl_files):
    file_paths = mock_jsonl_files
    with open(file_paths[0], "w", encoding="utf-8") as f:
        f.write("Invalid JSON entry\n")
    cognitive_journal._dir = os.path.dirname(mock_jsonl_files[0])
    cognitive_journal._load()
    assert len(cognitive_journal.get_entries()) == 35