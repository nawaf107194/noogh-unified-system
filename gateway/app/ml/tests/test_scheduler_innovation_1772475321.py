import pytest
from unittest.mock import patch, MagicMock

class MockPersistenceFile:
    def __init__(self, exists_value):
        self.exists_value = exists_value
        self.open_mode = None

    def exists(self):
        return self.exists_value

    def open(self, mode):
        self.open_mode = mode
        return self

    def read(self):
        return '{"task": "example"}'

class MockQueue:
    def __init__(self):
        self.queue = []

def test_load_queue_happy_path(tmpdir):
    persistence_file = tmpdir.join("queue.json")
    persistence_file.write('{"task": "example"}')
    
    scheduler = Scheduler(persistence_file)
    scheduler._load_queue()
    
    assert scheduler.queue == [{"task": "example"}]

@patch.object(Scheduler, 'persistence_file', new_callable=MagicMock(return_value=MockPersistenceFile(True)))
def test_load_queue_edge_case_empty_content(mock_persistence_file):
    mock_persistence_file.return_value.read.return_value = '{}'
    
    scheduler = Scheduler(None)
    scheduler._load_queue()
    
    assert scheduler.queue == []

@patch.object(Scheduler, 'persistence_file', new_callable=MagicMock(return_value=MockPersistenceFile(False)))
def test_load_queue_edge_case_non_existent(mock_persistence_file):
    
    scheduler = Scheduler(None)
    scheduler._load_queue()
    
    assert scheduler.queue == []

@patch.object(Scheduler, 'persistence_file', new_callable=MagicMock(return_value=MockPersistenceFile(True)))
def test_load_queue_error_case_invalid_json(mock_persistence_file):
    mock_persistence_file.return_value.read.return_value = '{"task": "example"'

    scheduler = Scheduler(None)
    scheduler._load_queue()
    
    assert scheduler.queue == []

class Scheduler:
    def __init__(self, persistence_file):
        self.persistence_file = persistence_file
        self.queue = []