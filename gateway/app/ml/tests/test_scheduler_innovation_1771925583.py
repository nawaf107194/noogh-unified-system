import pytest
from gateway.app.ml.scheduler import Scheduler
import json
from pathlib import Path

class MockPersistenceFile(Path):
    def exists(self):
        return True

    def open(self, mode):
        if mode == "r":
            return MockFileHandle("[]")
        else:
            raise IOError("Mock file handle does not support write mode")

class MockFileHandle:
    def __init__(self, content):
        self.content = content
        self.pos = 0

    def read(self):
        result = self.content[self.pos:]
        self.pos = len(self.content)
        return result

    def close(self):
        pass

def test_load_queue_happy_path(tmpdir):
    scheduler = Scheduler(persistence_file=MockPersistenceFile(tmpdir / "queue.json"))
    assert scheduler.queue == []

def test_load_queue_empty_file(tmpdir):
    (tmpdir / "queue.json").write_text("[]")
    scheduler = Scheduler(persistence_file=MockPersistenceFile(tmpdir / "queue.json"))
    assert scheduler.queue == []

def test_load_queue_valid_json(tmpdir):
    data = [{"task": "train", "model": "resnet"}]
    (tmpdir / "queue.json").write_text(json.dumps(data))
    scheduler = Scheduler(persistence_file=MockPersistenceFile(tmpdir / "queue.json"))
    assert scheduler.queue == [{"task": "train", "model": "resnet"}]

def test_load_queue_invalid_json(tmpdir):
    (tmpdir / "queue.json").write_text("invalid json")
    scheduler = Scheduler(persistence_file=MockPersistenceFile(tmpdir / "queue.json"))
    assert scheduler.queue == []

def test_load_queue_missing_file(tmpdir):
    scheduler = Scheduler(persistence_file=MockPersistenceFile(tmpdir / "nonexistent.json"))
    assert scheduler.queue == []