import pytest
from gateway.app.security.hmac_logger import HMACLogger, AuditEvent

@pytest.fixture
def hmac_logger(tmp_path):
    log_file = tmp_path / "audit.log"
    logger = HMACLogger(str(log_file))
    yield logger

def test_happy_path(hmac_logger, tmp_path):
    # Create a valid audit log with 3 events
    lines = [
        '{"event_type": "login", "hmac_signature": "valid_hash_1"}\n',
        '{"event_type": "logout", "previous_hash": "valid_hash_1", "hmac_signature": "valid_hash_2"}\n',
        '{"event_type": "access", "previous_hash": "valid_hash_2", "hmac_signature": "valid_hash_3"}\n'
    ]
    with open(tmp_path / "audit.log", "w") as f:
        f.writelines(lines)

    result = hmac_logger.verify_log()
    assert result == {
        "valid": True,
        "events_checked": 3,
        "tampered_events": [],
        "chain_broken": [],
        "message": "Log is valid"
    }

def test_empty_log(hmac_logger, tmp_path):
    with open(tmp_path / "audit.log", "w") as f:
        pass

    result = hmac_logger.verify_log()
    assert result == {
        "valid": True,
        "events_checked": 0,
        "message": "Empty log"
    }

def test_invalid_json(hmac_logger, tmp_path):
    lines = [
        '{"event_type": "login", "hmac_signature": "valid_hash_1"}\n',
        'not valid json\n',
        '{"event_type": "access", "previous_hash": "valid_hash_2", "hmac_signature": "valid_hash_3"}\n'
    ]
    with open(tmp_path / "audit.log", "w") as f:
        f.writelines(lines)

    result = hmac_logger.verify_log()
    assert result == {
        "valid": False,
        "events_checked": 3,
        "tampered_events": [2],
        "chain_broken": [],
        "message": "TAMPERING DETECTED"
    }

def test_file_not_found(hmac_logger, tmp_path):
    hmac_logger.log_file = str(tmp_path / "nonexistent_log.log")
    result = hmac_logger.verify_log()
    assert result == {
        "valid": True,
        "events_checked": 0,
        "message": "No log file"
    }

def test_invalid_event_type(hmac_logger, tmp_path):
    lines = [
        '{"event_type": "invalid", "hmac_signature": "valid_hash_1"}\n'
    ]
    with open(tmp_path / "audit.log", "w") as f:
        f.writelines(lines)

    result = hmac_logger.verify_log()
    assert result == {
        "valid": False,
        "events_checked": 1,
        "tampered_events": [1],
        "chain_broken": [],
        "message": "TAMPERING DETECTED"
    }

def test_invalid_previous_hash(hmac_logger, tmp_path):
    lines = [
        '{"event_type": "login", "hmac_signature": "valid_hash_1"}\n',
        '{"event_type": "logout", "previous_hash": "invalid_hash", "hmac_signature": "valid_hash_2"}\n'
    ]
    with open(tmp_path / "audit.log", "w") as f:
        f.writelines(lines)

    result = hmac_logger.verify_log()
    assert result == {
        "valid": False,
        "events_checked": 2,
        "tampered_events": [],
        "chain_broken": [1],
        "message": "TAMPERING DETECTED"
    }