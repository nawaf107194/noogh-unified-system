import pytest
import os

from gateway.app.core.jobs import Jobs

def test_init_happy_path(tmpdir):
    base_dir = str(tmpdir.mkdir("test_base"))
    jobs = Jobs(base_dir)
    assert jobs.base_dir == base_dir
    assert os.path.exists(base_dir)
    assert os.path.exists(os.path.join(base_dir, "queue.jsonl"))

def test_init_empty_string():
    with pytest.raises(ValueError) as exc_info:
        Jobs("")
    assert str(exc_info.value) == "Base directory cannot be empty"

def test_init_none():
    with pytest.raises(ValueError) as exc_info:
        Jobs(None)
    assert str(exc_info.value) == "Base directory cannot be None"

def test_init_invalid_path(tmp_path):
    invalid_path = os.path.join(str(tmp_path), "non-existent-dir", "jobs")
    with pytest.raises(FileNotFoundError) as exc_info:
        Jobs(invalid_path)
    assert str(exc_info.value) == f"No such file or directory: '{invalid_path}'"