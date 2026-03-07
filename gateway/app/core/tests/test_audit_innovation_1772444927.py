import pytest
from gateway.app.core.audit import Audit, file_lock
import hashlib
from datetime import datetime
import json
import os

class MockFileLock:
    def __enter__(self):
        pass
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.fixture
def audit_instance(tmp_path):
    log_file = tmp_path / "audit.log"
    return Audit(log_file)

def test_log_task_happy_path(audit_instance, tmp_path):
    task_id = "12345"
    input_text = "test input"
    protocol_result = "success"
    exec_summary = "task completed successfully"

    audit_instance.log_task(task_id, input_text, protocol_result, exec_summary)
    
    with open(tmp_path / "audit.log", "r") as f:
        content = f.read()
        records = json.loads(content.strip().replace("\n", ","))
    
    assert len(records) == 1
    record = records[0]
    assert record["task_id"] == task_id
    assert record["input_sha256"] == hashlib.sha256(input_text.encode()).hexdigest()
    assert record["protocol_result"] == protocol_result
    assert record["exec_summary"] == exec_summary

def test_log_task_empty_input(audit_instance, tmp_path):
    task_id = "12345"
    input_text = ""
    protocol_result = "success"
    exec_summary = "task completed successfully"

    audit_instance.log_task(task_id, input_text, protocol_result, exec_summary)
    
    with open(tmp_path / "audit.log", "r") as f:
        content = f.read()
        records = json.loads(content.strip().replace("\n", ","))
    
    assert len(records) == 1
    record = records[0]
    assert record["input_sha256"] == hashlib.sha256(input_text.encode()).hexdigest()

def test_log_task_none_input(audit_instance, tmp_path):
    task_id = "12345"
    input_text = None
    protocol_result = "success"
    exec_summary = "task completed successfully"

    audit_instance.log_task(task_id, input_text, protocol_result, exec_summary)
    
    with open(tmp_path / "audit.log", "r") as f:
        content = f.read()
        records = json.loads(content.strip().replace("\n", ","))
    
    assert len(records) == 1
    record = records[0]
    assert record["input_sha256"] == hashlib.sha256(b"").hexdigest()

def test_log_task_boundary_input(audit_instance, tmp_path):
    task_id = "12345"
    input_text = "a" * 1024 * 1024  # 1MB of 'a'
    protocol_result = "success"
    exec_summary = "task completed successfully"

    audit_instance.log_task(task_id, input_text, protocol_result, exec_summary)
    
    with open(tmp_path / "audit.log", "r") as f:
        content = f.read()
        records = json.loads(content.strip().replace("\n", ","))
    
    assert len(records) == 1
    record = records[0]
    assert record["input_sha256"] == hashlib.sha256(input_text.encode()).hexdigest()

def test_log_task_invalid_input(audit_instance, tmp_path):
    task_id = "12345"
    input_text = None
    protocol_result = "success"
    exec_summary = 123

    audit_instance.log_task(task_id, input_text, protocol_result, exec_summary)
    
    with open(tmp_path / "audit.log", "r") as f:
        content = f.read()
        records = json.loads(content.strip().replace("\n", ","))
    
    assert len(records) == 1
    record = records[0]
    assert record["input_sha256"] == hashlib.sha256(b"").hexdigest()

def test_log_task_async_behavior(audit_instance, tmp_path):
    task_id = "12345"
    input_text = "test input"
    protocol_result = "success"
    exec_summary = "task completed successfully"

    audit_instance.log_task(task_id, input_text, protocol_result, exec_summary)
    
    with open(tmp_path / "audit.log", "r") as f:
        content = f.read()
        records = json.loads(content.strip().replace("\n", ","))
    
    assert len(records) == 1
    record = records[0]
    assert record["task_id"] == task_id
    assert record["input_sha256"] == hashlib.sha256(input_text.encode()).hexdigest()
    assert record["protocol_result"] == protocol_result
    assert record["exec_summary"] == exec_summary