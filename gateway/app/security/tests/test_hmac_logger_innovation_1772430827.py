import pytest
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, Any

class MockHMACLogger:
    def __init__(self):
        self.log_file = "mock_log.txt"
        with open(self.log_file, "w") as f:
            f.write('{"event_id": "1", "timestamp": 1633072800}')
            f.write('\n')
            f.write('{"event_id": "2", "timestamp": 1633072801}')

    def verify_event(self, event):
        return True

def test_get_integrity_proof_happy_path():
    logger = MockHMACLogger()
    hmac_logger = HMACLogger(logger.log_file)
    result = hmac_logger.get_integrity_proof("1")
    assert result is not None
    assert result["event"]["event_id"] == "1"
    assert result["verified"]
    assert datetime.strptime(result["timestamp_readable"], "%Y-%m-%d %H:%M:%S")

def test_get_integrity_proof_empty_log():
    with open("mock_log.txt", "w") as f:
        pass
    hmac_logger = HMACLogger("mock_log.txt")
    result = hmac_logger.get_integrity_proof("1")
    assert result is None

def test_get_integrity_proof_non_existent_event():
    logger = MockHMACLogger()
    hmac_logger = HMACLogger(logger.log_file)
    result = hmac_logger.get_integrity_proof("3")
    assert result is None

def test_get_integrity_proof_invalid_input():
    hmac_logger = HMACLogger("mock_log.txt")
    with pytest.raises(TypeError):
        hmac_logger.get_integrity_proof(None)