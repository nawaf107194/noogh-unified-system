import pytest

from gateway.app.core.audit import get_audit_logger, AuditLogger

def test_get_audit_logger_happy_path():
    data_dir = "/path/to/data"
    logger = get_audit_logger(data_dir)
    assert isinstance(logger, AuditLogger)
    assert logger.data_dir == data_dir

def test_get_audit_logger_empty_data_dir():
    data_dir = ""
    logger = get_audit_logger(data_dir)
    assert logger is None or logger.data_dir == ""

def test_get_audit_logger_none_data_dir():
    data_dir = None
    logger = get_audit_logger(data_dir)
    assert logger is None or logger.data_dir is None

def test_get_audit_logger_boundary_data_dir():
    data_dir = "/"
    logger = get_audit_logger(data_dir)
    assert isinstance(logger, AuditLogger)
    assert logger.data_dir == "/"

# Assuming there are no error cases in the provided code