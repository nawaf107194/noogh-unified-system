import os
import time
from typing import Optional
import shutil
import uuid
import hashlib
import json
from unittest.mock import patch
from src.gateway.app.core.artifact_registry import ArtifactRegistry, register, ArtifactRecord

@pytest.fixture
def artifact_registry():
    data_dir = "/tmp/test_artifact_registry"
    index_file = os.path.join(data_dir, "index.json")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    registry = ArtifactRegistry(data_dir=data_dir, index_file=index_file)
    yield registry
    shutil.rmtree(data_dir)

def test_register_happy_path(artifact_registry):
    relative_path = "test_artifact.txt"
    with open(os.path.join(artifact_registry.data_dir, relative_path), "wb") as f:
        f.write(b"some content")

    record = register(type="text/plain", relative_path=relative_path, artifact_registry=artifact_registry)

    assert isinstance(record, ArtifactRecord)
    assert record.type == "text/plain"
    assert record.path == relative_path
    assert os.path.exists(os.path.join(artifact_registry.data_dir, record.artifact_id))

def test_register_empty_relative_path(artifact_registry):
    with pytest.raises(FileNotFoundError) as exc_info:
        register(type="text/plain", relative_path="", artifact_registry=artifact_registry)
    assert "Artifact not found" in str(exc_info.value)

def test_register_none_relative_path(artifact_registry):
    with pytest.raises(FileNotFoundError) as exc_info:
        register(type="text/plain", relative_path=None, artifact_registry=artifact_registry)
    assert "Artifact not found" in str(exc_info.value)

def test_register_invalid_type(artifact_registry):
    relative_path = "test_artifact.txt"
    with open(os.path.join(artifact_registry.data_dir, relative_path), "wb") as f:
        f.write(b"some content")

    record = register(type="invalid/type", relative_path=relative_path, artifact_registry=artifact_registry)

    assert isinstance(record, ArtifactRecord)
    assert record.type == "invalid/type"

def test_register_session_id(artifact_registry):
    relative_path = "test_artifact.txt"
    with open(os.path.join(artifact_registry.data_dir, relative_path), "wb") as f:
        f.write(b"some content")

    record = register(type="text/plain", relative_path=relative_path, session_id="session123", artifact_registry=artifact_registry)

    assert isinstance(record, ArtifactRecord)
    assert record.session_id == "session123"

def test_register_job_id(artifact_registry):
    relative_path = "test_artifact.txt"
    with open(os.path.join(artifact_registry.data_dir, relative_path), "wb") as f:
        f.write(b"some content")

    record = register(type="text/plain", relative_path=relative_path, job_id="job123", artifact_registry=artifact_registry)

    assert isinstance(record, ArtifactRecord)
    assert record.job_id == "job123"

def test_register_index_file(artifact_registry):
    relative_path = "test_artifact.txt"
    with open(os.path.join(artifact_registry.data_dir, relative_path), "wb") as f:
        f.write(b"some content")

    register(type="text/plain", relative_path=relative_path, artifact_registry=artifact_registry)

    assert os.path.exists(artifact_registry.index_file)