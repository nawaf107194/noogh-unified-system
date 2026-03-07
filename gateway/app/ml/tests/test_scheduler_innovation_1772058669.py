import pytest
from unittest.mock import patch, MagicMock

class MockScheduler:
    def __init__(self):
        self.persistence_file = "mock_persistence_file.json"
        self.queue = []

    @patch('builtins.open')
    def _load_queue(self, mock_open):
        with open(self.persistence_file, "r") as f:
            self.queue = json.load(f)

def test_load_queue_happy_path(monkeypatch):
    scheduler = MockScheduler()
    mock_data = {"item": "test"}
    monkeypatch.setattr('builtins.open', lambda *args, **kwargs: MagicMock(read=lambda: str(mock_data)))
    scheduler._load_queue()
    assert scheduler.queue == [{"item": "test"}]

def test_load_queue_empty_file(monkeypatch):
    scheduler = MockScheduler()
    monkeypatch.setattr('builtins.open', lambda *args, **kwargs: MagicMock(read=lambda: '{}'))
    scheduler._load_queue()
    assert scheduler.queue == []

def test_load_queue_invalid_json(monkeypatch):
    scheduler = MockScheduler()
    invalid_data = "invalid json"
    monkeypatch.setattr('builtins.open', lambda *args, **kwargs: MagicMock(read=lambda: invalid_data))
    with patch.object(logger, 'error') as mock_error:
        scheduler._load_queue()
        assert scheduler.queue == []
        mock_error.assert_called_once()

def test_load_queue_file_not_found(monkeypatch):
    scheduler = MockScheduler()
    monkeypatch.setattr('builtins.open', lambda *args, **kwargs: MagicMock(side_effect=FileNotFoundError))
    with patch.object(logger, 'error') as mock_error:
        scheduler._load_queue()
        assert scheduler.queue == []
        mock_error.assert_called_once()