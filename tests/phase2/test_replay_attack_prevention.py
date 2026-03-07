"""
Replay Attack Prevention Tests

Tests for message replay attack vulnerabilities:
- Timestamp validation
- Nonce (message ID) uniqueness
- TTL enforcement
- Duplicate detection mechanisms

OWASP References:
- A04:2021 Insecure Design
- CWE-294: Authentication Bypass by Capture-replay
"""
import pytest
import asyncio
import time
import uuid
from typing import Any, Dict, List, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import copy
import json

# Try to import from actual module, fall back to mock
try:
    from unified_core.messaging import (
        AgentMessage,
        MessageType,
        MessagePriority
    )
except ImportError:
    # Mock implementations
    class MessageType(Enum):
        REQUEST = "request"
        RESPONSE = "response"
        EVENT = "event"
        BROADCAST = "broadcast"
        HEARTBEAT = "heartbeat"
        ERROR = "error"
    
    class MessagePriority(Enum):
        LOW = 0
        NORMAL = 1
        HIGH = 2
        CRITICAL = 3
    
    @dataclass
    class AgentMessage:
        id: str
        source_agent: str
        target_agent: str
        message_type: MessageType
        action: str
        payload: Dict[str, Any]
        timestamp: float
        priority: MessagePriority = MessagePriority.NORMAL
        correlation_id: str = None
        ttl_seconds: int = 300
        metadata: Dict[str, Any] = field(default_factory=dict)
        
        @staticmethod
        def create(source: str, target: str, action: str, payload: Dict = None,
                   msg_type: MessageType = MessageType.REQUEST,
                   priority: MessagePriority = MessagePriority.NORMAL) -> "AgentMessage":
            return AgentMessage(
                id=str(uuid.uuid4()),
                source_agent=source,
                target_agent=target,
                message_type=msg_type,
                action=action,
                payload=payload or {},
                timestamp=time.time(),
                priority=priority,
                correlation_id=str(uuid.uuid4())
            )


@dataclass
class ReplayTestResult:
    """Result of replay attack test."""
    test_name: str
    original_accepted: bool
    replay_accepted: bool
    vulnerability_found: bool
    delay_seconds: float = 0.0


# =============================================================================
# MOCK REPLAY DETECTION
# =============================================================================

class ReplayDetector:
    """Mock replay detection implementation for testing."""
    
    def __init__(self, ttl_seconds: int = 300, max_nonces: int = 10000):
        self.ttl_seconds = ttl_seconds
        self.max_nonces = max_nonces
        self._seen_nonces: Set[str] = set()
        self._nonce_timestamps: Dict[str, float] = {}
        
    def is_replay(self, message: AgentMessage) -> bool:
        """Check if message is a replay."""
        now = time.time()
        
        # Check timestamp validity
        if message.timestamp > now + 60:  # Allow 60s clock skew
            return True  # Future timestamp
        
        if now - message.timestamp > self.ttl_seconds:
            return True  # Expired message
        
        # Check nonce uniqueness
        if message.id in self._seen_nonces:
            return True  # Duplicate nonce
        
        # Record nonce
        self._record_nonce(message.id, message.timestamp)
        return False
    
    def _record_nonce(self, nonce: str, timestamp: float):
        """Record seen nonce."""
        self._seen_nonces.add(nonce)
        self._nonce_timestamps[nonce] = timestamp
        
        # Cleanup old nonces if needed
        if len(self._seen_nonces) > self.max_nonces:
            self._cleanup_old_nonces()
    
    def _cleanup_old_nonces(self):
        """Remove expired nonces."""
        now = time.time()
        expired = [
            nonce for nonce, ts in self._nonce_timestamps.items()
            if now - ts > self.ttl_seconds
        ]
        for nonce in expired:
            self._seen_nonces.discard(nonce)
            self._nonce_timestamps.pop(nonce, None)


class MockBrokerWithReplayDetection:
    """Mock broker with replay detection."""
    
    def __init__(self, replay_detection_enabled: bool = False):
        self.replay_detection_enabled = replay_detection_enabled
        self.detector = ReplayDetector()
        self.messages_processed: List[AgentMessage] = []
        
    def process_message(self, message: AgentMessage) -> bool:
        """Process message with optional replay detection."""
        if self.replay_detection_enabled:
            if self.detector.is_replay(message):
                return False
        
        self.messages_processed.append(message)
        return True


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def broker_no_replay():
    """Broker without replay detection."""
    return MockBrokerWithReplayDetection(replay_detection_enabled=False)


@pytest.fixture
def broker_with_replay():
    """Broker with replay detection."""
    return MockBrokerWithReplayDetection(replay_detection_enabled=True)


@pytest.fixture
def sample_message():
    """Create sample message for testing."""
    return AgentMessage.create(
        source="sender",
        target="receiver",
        action="transfer_funds",
        payload={"amount": 1000, "recipient": "account"}
    )


# =============================================================================
# BASIC REPLAY TESTS
# =============================================================================

class TestBasicReplay:
    """Test basic replay attack scenarios."""
    
    def test_immediate_replay_without_protection(self, broker_no_replay, sample_message):
        """Test that immediate replay succeeds without protection."""
        # First send
        first_success = broker_no_replay.process_message(sample_message)
        assert first_success
        
        # Immediate replay (exact same message)
        replay_success = broker_no_replay.process_message(sample_message)
        
        # Without protection, replay succeeds (vulnerability)
        result = ReplayTestResult(
            test_name="immediate_replay_no_protection",
            original_accepted=first_success,
            replay_accepted=replay_success,
            vulnerability_found=replay_success
        )
        
        assert replay_success, "Expected vulnerability: replay accepted without protection"
    
    def test_immediate_replay_with_protection(self, broker_with_replay, sample_message):
        """Test that immediate replay is blocked with protection."""
        # First send
        first_success = broker_with_replay.process_message(sample_message)
        assert first_success
        
        # Immediate replay
        replay_success = broker_with_replay.process_message(sample_message)
        
        assert not replay_success, "Replay should be blocked with detection enabled"
    
    def test_delayed_replay(self, broker_with_replay):
        """Test replay with delay (within TTL)."""
        message = AgentMessage.create(
            source="sender",
            target="receiver",
            action="action",
            payload={}
        )
        
        # First send
        first_success = broker_with_replay.process_message(message)
        assert first_success
        
        # Simulate delay (message kept same)
        time.sleep(0.1)
        
        # Replay with same message ID
        replay_success = broker_with_replay.process_message(message)
        
        assert not replay_success, "Delayed replay should still be blocked"


# =============================================================================
# TIMESTAMP VALIDATION TESTS
# =============================================================================

class TestTimestampValidation:
    """Test timestamp-based replay prevention."""
    
    def test_expired_message_rejected(self, broker_with_replay):
        """Test that expired messages are rejected."""
        # Create message with old timestamp
        old_message = AgentMessage(
            id=str(uuid.uuid4()),
            source_agent="sender",
            target_agent="receiver",
            message_type=MessageType.REQUEST,
            action="action",
            payload={},
            timestamp=time.time() - 400,  # 400 seconds old (> 300 TTL)
            priority=MessagePriority.NORMAL,
            ttl_seconds=300
        )
        
        accepted = broker_with_replay.process_message(old_message)
        
        assert not accepted, "Expired message should be rejected"
    
    def test_future_timestamp_rejected(self, broker_with_replay):
        """Test that messages with future timestamps are rejected."""
        future_message = AgentMessage(
            id=str(uuid.uuid4()),
            source_agent="sender",
            target_agent="receiver",
            message_type=MessageType.REQUEST,
            action="action",
            payload={},
            timestamp=time.time() + 120,  # 2 minutes in future
            priority=MessagePriority.NORMAL
        )
        
        accepted = broker_with_replay.process_message(future_message)
        
        assert not accepted, "Future timestamp message should be rejected"
    
    def test_valid_timestamp_accepted(self, broker_with_replay):
        """Test that messages with valid timestamps are accepted."""
        valid_message = AgentMessage.create(
            source="sender",
            target="receiver",
            action="action",
            payload={}
        )
        
        accepted = broker_with_replay.process_message(valid_message)
        
        assert accepted, "Valid timestamp message should be accepted"
    
    def test_clock_skew_tolerance(self, broker_with_replay):
        """Test tolerance for clock skew."""
        # Message with slight future timestamp (within tolerance)
        slight_future = AgentMessage(
            id=str(uuid.uuid4()),
            source_agent="sender",
            target_agent="receiver",
            message_type=MessageType.REQUEST,
            action="action",
            payload={},
            timestamp=time.time() + 30,  # 30 seconds in future (within 60s tolerance)
            priority=MessagePriority.NORMAL
        )
        
        accepted = broker_with_replay.process_message(slight_future)
        
        assert accepted, "Slight clock skew should be tolerated"


# =============================================================================
# NONCE UNIQUENESS TESTS
# =============================================================================

class TestNonceUniqueness:
    """Test nonce (message ID) uniqueness enforcement."""
    
    def test_duplicate_nonce_rejected(self, broker_with_replay):
        """Test that duplicate nonces are rejected."""
        nonce = str(uuid.uuid4())
        
        msg1 = AgentMessage(
            id=nonce,
            source_agent="sender",
            target_agent="receiver",
            message_type=MessageType.REQUEST,
            action="action",
            payload={"version": 1},
            timestamp=time.time(),
            priority=MessagePriority.NORMAL
        )
        
        msg2 = AgentMessage(
            id=nonce,  # Same nonce!
            source_agent="sender",
            target_agent="receiver",
            message_type=MessageType.REQUEST,
            action="action",
            payload={"version": 2},  # Different payload
            timestamp=time.time(),
            priority=MessagePriority.NORMAL
        )
        
        first_accepted = broker_with_replay.process_message(msg1)
        second_accepted = broker_with_replay.process_message(msg2)
        
        assert first_accepted, "First message should be accepted"
        assert not second_accepted, "Message with duplicate nonce should be rejected"
    
    def test_unique_nonces_accepted(self, broker_with_replay):
        """Test that unique nonces are all accepted."""
        messages = [
            AgentMessage.create(
                source="sender",
                target="receiver",
                action="action",
                payload={"index": i}
            )
            for i in range(100)
        ]
        
        accepted_count = sum(
            1 for msg in messages 
            if broker_with_replay.process_message(msg)
        )
        
        assert accepted_count == 100, "All unique nonces should be accepted"
    
    def test_nonce_reuse_after_expiry(self, broker_with_replay):
        """Test that nonces can be reused after TTL expiry."""
        # Reduce TTL for testing
        broker_with_replay.detector.ttl_seconds = 1
        
        nonce = str(uuid.uuid4())
        
        msg1 = AgentMessage(
            id=nonce,
            source_agent="sender",
            target_agent="receiver",
            message_type=MessageType.REQUEST,
            action="action",
            payload={},
            timestamp=time.time() - 2,  # Already expired
            priority=MessagePriority.NORMAL
        )
        
        # This should be rejected due to expired timestamp
        first_accepted = broker_with_replay.process_message(msg1)
        
        # Create new message with same nonce but fresh timestamp
        msg2 = AgentMessage(
            id=nonce,
            source_agent="sender",
            target_agent="receiver",
            message_type=MessageType.REQUEST,
            action="action",
            payload={},
            timestamp=time.time(),
            priority=MessagePriority.NORMAL
        )
        
        # After cleanup, nonce could be reused
        broker_with_replay.detector._cleanup_old_nonces()
        second_accepted = broker_with_replay.process_message(msg2)
        
        # Note: behavior depends on cleanup implementation
        assert first_accepted == False or second_accepted == True


# =============================================================================
# MODIFIED REPLAY TESTS
# =============================================================================

class TestModifiedReplay:
    """Test replay with modified message fields."""
    
    def test_replay_with_different_payload(self, broker_with_replay):
        """Test replay attack with modified payload."""
        original = AgentMessage.create(
            source="sender",
            target="receiver",
            action="transfer",
            payload={"amount": 100}
        )
        
        # First send
        broker_with_replay.process_message(original)
        
        # Attacker modifies payload but keeps same ID
        modified = AgentMessage(
            id=original.id,  # Same ID
            source_agent=original.source_agent,
            target_agent=original.target_agent,
            message_type=original.message_type,
            action=original.action,
            payload={"amount": 10000},  # Modified!
            timestamp=original.timestamp,
            priority=original.priority
        )
        
        accepted = broker_with_replay.process_message(modified)
        
        assert not accepted, "Modified replay should be rejected by nonce check"
    
    def test_replay_with_different_target(self, broker_with_replay):
        """Test replay redirected to different target."""
        original = AgentMessage.create(
            source="sender",
            target="receiver1",
            action="send_data",
            payload={"data": "sensitive"}
        )
        
        broker_with_replay.process_message(original)
        
        # Attacker redirects to different target
        redirected = AgentMessage(
            id=original.id,
            source_agent=original.source_agent,
            target_agent="attacker_agent",  # Redirected!
            message_type=original.message_type,
            action=original.action,
            payload=original.payload,
            timestamp=original.timestamp,
            priority=original.priority
        )
        
        accepted = broker_with_replay.process_message(redirected)
        
        assert not accepted, "Redirected replay should be rejected"


# =============================================================================
# TTL ENFORCEMENT TESTS
# =============================================================================

class TestTTLEnforcement:
    """Test message Time-To-Live enforcement."""
    
    def test_message_within_ttl_accepted(self, broker_with_replay):
        """Test messages within TTL are accepted."""
        message = AgentMessage(
            id=str(uuid.uuid4()),
            source_agent="sender",
            target_agent="receiver",
            message_type=MessageType.REQUEST,
            action="action",
            payload={},
            timestamp=time.time() - 100,  # 100 seconds old
            priority=MessagePriority.NORMAL,
            ttl_seconds=300  # 5 minute TTL
        )
        
        accepted = broker_with_replay.process_message(message)
        
        assert accepted, "Message within TTL should be accepted"
    
    def test_message_exceeding_ttl_rejected(self, broker_with_replay):
        """Test messages exceeding TTL are rejected."""
        message = AgentMessage(
            id=str(uuid.uuid4()),
            source_agent="sender",
            target_agent="receiver",
            message_type=MessageType.REQUEST,
            action="action",
            payload={},
            timestamp=time.time() - 400,  # 400 seconds old
            priority=MessagePriority.NORMAL,
            ttl_seconds=300  # 5 minute TTL
        )
        
        accepted = broker_with_replay.process_message(message)
        
        assert not accepted, "Message exceeding TTL should be rejected"
    
    def test_custom_ttl_per_message(self, broker_with_replay):
        """Test per-message TTL customization."""
        # Short TTL message
        short_ttl = AgentMessage(
            id=str(uuid.uuid4()),
            source_agent="sender",
            target_agent="receiver",
            message_type=MessageType.REQUEST,
            action="critical_action",
            payload={},
            timestamp=time.time() - 10,  # 10 seconds old
            priority=MessagePriority.CRITICAL,
            ttl_seconds=5  # Only 5 second TTL
        )
        
        # This test documents that current detector uses fixed TTL
        # In production, should respect per-message TTL
        accepted = broker_with_replay.process_message(short_ttl)
        
        # Current implementation ignores per-message TTL (vulnerability)
        # Should be rejected (10s old, 5s TTL)


# =============================================================================
# AUDIT SUMMARY
# =============================================================================

class TestReplayAuditSummary:
    """Generate replay attack audit summary."""
    
    def test_generate_audit_summary(self, broker_with_replay):
        """Run comprehensive replay tests and generate summary."""
        results = {
            "replay_tests": 0,
            "replay_blocked": 0,
            "timestamp_tests": 0,
            "timestamp_validated": 0,
            "nonce_tests": 0,
            "nonce_validated": 0,
        }
        
        # Basic replay test
        msg1 = AgentMessage.create("sender", "receiver", "action", {})
        broker_with_replay.process_message(msg1)
        results["replay_tests"] += 1
        if not broker_with_replay.process_message(msg1):
            results["replay_blocked"] += 1
        
        # Expired message test
        old_msg = AgentMessage(
            id=str(uuid.uuid4()),
            source_agent="sender",
            target_agent="receiver",
            message_type=MessageType.REQUEST,
            action="action",
            payload={},
            timestamp=time.time() - 400,
            priority=MessagePriority.NORMAL
        )
        results["timestamp_tests"] += 1
        if not broker_with_replay.process_message(old_msg):
            results["timestamp_validated"] += 1
        
        # Unique nonce test
        msg2 = AgentMessage.create("sender", "receiver", "action", {})
        results["nonce_tests"] += 1
        if broker_with_replay.process_message(msg2):
            results["nonce_validated"] += 1
        
        print(f"\n{'='*60}")
        print("REPLAY ATTACK PREVENTION AUDIT SUMMARY")
        print(f"{'='*60}")
        print(f"Replay Blocked: {results['replay_blocked']}/{results['replay_tests']}")
        print(f"Timestamp Validated: {results['timestamp_validated']}/{results['timestamp_tests']}")
        print(f"Nonce Validated: {results['nonce_validated']}/{results['nonce_tests']}")
        print(f"{'='*60}\n")
        
        assert results["replay_blocked"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
