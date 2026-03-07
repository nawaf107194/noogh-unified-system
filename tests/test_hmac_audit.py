"""
P1.9 Tests - HMAC Audit Log Integrity
Tests tamper detection and verification capabilities.
"""
import pytest
import tempfile
import os
import json
from gateway.app.security.hmac_logger import HMACLogger, AuditEvent


class TestHMACLogger:
    """Test suite for P1.9 HMAC audit logging."""
    
    @pytest.fixture
    def secret_key(self):
        """Generate a test secret key."""
        return b"test-secret-key-32-bytes-long!!"
    
    @pytest.fixture
    def temp_log(self, tmp_path):
        """Create a temporary log file."""
        return str(tmp_path / "test_audit.log")
    
    @pytest.fixture
    def logger(self, secret_key, temp_log):
        """Create HMACLogger instance."""
        return HMACLogger(secret_key, temp_log)
    
    def test_secret_key_validation(self):
        """Secret key must be at least 16 bytes."""
        with pytest.raises(ValueError, match="at least 16 bytes"):
            HMACLogger(b"short", "test.log")
    
    def test_log_event_creates_signature(self, logger, temp_log):
        """Logging an event should create HMAC signature."""
        event = logger.log_event("evt-1", "test_event", {"data": "test"})
        
        assert event.hmac_signature is not None
        assert len(event.hmac_signature) == 64  # SHA256 hex = 64 chars
        assert event.event_id == "evt-1"
    
    def test_verify_valid_event(self, logger):
        """Valid events should pass verification."""
        event = logger.log_event("evt-1", "test", {"x": 1})
        assert logger.verify_event(event) is True
    
    def test_verify_tampered_payload(self, logger):
        """Tampering with payload should fail verification."""
        event = logger.log_event("evt-1", "test", {"data": "original"})
        
        # Tamper with payload
        event.payload["data"] = "tampered"
        
        assert logger.verify_event(event) is False
    
    def test_verify_tampered_signature(self, logger):
        """Tampering with signature should fail verification."""
        event = logger.log_event("evt-1", "test", {"data": "test"})
        
        # Tamper with signature
        event.hmac_signature = "0" * 64
        
        assert logger.verify_event(event) is False
    
    def test_event_chaining(self, logger):
        """Events should be chained to previous event."""
        event1 = logger.log_event("evt-1", "test", {"seq": 1})
        event2 = logger.log_event("evt-2", "test", {"seq": 2})
        event3 = logger.log_event("evt-3", "test", {"seq": 3})
        
        # Chain verification
        assert event1.previous_hash is None  # First event
        assert event2.previous_hash == event1.hmac_signature
        assert event3.previous_hash == event2.hmac_signature
    
    def test_verify_log_all_valid(self, logger, temp_log):
        """Verify entire log with no tampering."""
        # Create multiple events
        for i in range(5):
            logger.log_event(f"evt-{i}", "test", {"index": i})
        
        result = logger.verify_log()
        
        assert result["valid"] is True
        assert result["events_checked"] == 5
        assert len(result["tampered_events"]) == 0
        assert len(result["chain_broken"]) == 0
    
    def test_verify_log_detects_tampering(self, logger, temp_log):
        """Verify log should detect tampered events."""
        # Create events
        for i in range(3):
            logger.log_event(f"evt-{i}", "test", {"index": i})
        
        # Tamper with second event in file
        with open(temp_log, 'r') as f:
            lines = f.readlines()
        
        # Modify payload of second event
        event2 = json.loads(lines[1])
        event2["payload"]["index"] = 99  # Tamper
        lines[1] = json.dumps(event2) + '\n'
        
        with open(temp_log, 'w') as f:
            f.writelines(lines)
        
        # Verify should detect tampering
        result = logger.verify_log()
        
        assert result["valid"] is False
        assert 2 in result["tampered_events"]  # Line 2 (1-indexed)
    
    def test_verify_log_detects_chain_break(self, logger, temp_log):
        """Verify log should detect broken chains."""
        # Create events
        event1 = logger.log_event("evt-1", "test", {"seq": 1})
        event2 = logger.log_event("evt-2", "test", {"seq": 2})
        
        # Manually break chain
        with open(temp_log, 'r') as f:
            lines = f.readlines()
        
        event2_data = json.loads(lines[1])
        event2_data["previous_hash"] = "BROKEN_HASH"
        lines[1] = json.dumps(event2_data) + '\n'
        
        with open(temp_log, 'w') as f:
            f.writelines(lines)
        
        result = logger.verify_log()
        
        assert result["valid"] is False
        assert 2 in result["chain_broken"]
    
    def test_get_integrity_proof(self, logger):
        """Should provide cryptographic proof for events."""
        event = logger.log_event("test-evt", "test", {"data": "proof"})
        
        proof = logger.get_integrity_proof("test-evt")
        
        assert proof is not None
        assert proof["verified"] is True
        assert proof["event"]["event_id"] == "test-evt"
        assert "timestamp_readable" in proof
    
    def test_get_integrity_proof_not_found(self, logger):
        """Should return None for non-existent events."""
        proof = logger.get_integrity_proof("nonexistent")
        assert proof is None
    
    def test_hmac_deterministic(self, logger):
        """Same data should always produce same HMAC."""
        signature1 = logger._compute_hmac("id", 123.0, "type", {"a": 1}, None)
        signature2 = logger._compute_hmac("id", 123.0, "type", {"a": 1}, None)
        
        assert signature1 == signature2
    
    def test_hmac_differs_with_change(self, logger):
        """Different data should produce different HMAC."""
        sig1 = logger._compute_hmac("id", 123.0, "type", {" a": 1}, None)
        sig2 = logger._compute_hmac("id", 123.0, "type", {"a": 2}, None)
        
        assert sig1 != sig2
    
    def test_empty_log_verification(self, logger, temp_log):
        """Empty log should be valid."""
        result = logger.verify_log()
        
        assert result["valid"] is True
        assert result["events_checked"] == 0
    
    def test_load_last_hash_on_restart(self, secret_key, temp_log):
        """Logger should load last hash when restarted."""
        # Create logger and add events
        logger1 = HMACLogger(secret_key, temp_log)
        event1 = logger1.log_event("evt-1", "test", {"seq": 1})
        event2 = logger1.log_event("evt-2", "test", {"seq": 2})
        
        # Create new logger instance (simulates restart)
        logger2 = HMACLogger(secret_key, temp_log)
        
        # Should have loaded last hash
        assert logger2.last_hash == event2.hmac_signature
        
        # Next event should chain correctly
        event3 = logger2.log_event("evt-3", "test", {"seq": 3})
        assert event3.previous_hash == event2.hmac_signature


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
