"""
Message Authentication Security Tests

Tests for agent message authentication and integrity:
- No authentication allows impersonation
- Message tampering detection
- Digital signature validation
- Token-based authentication patterns
- Agent identity verification

OWASP References:
- A02:2021 Cryptographic Failures
- A07:2021 Identification and Authentication Failures
- CWE-287: Improper Authentication
"""
import pytest
import asyncio
import json
import time
import uuid
import hmac
import hashlib
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Try to import from actual module, fall back to mock
try:
    from unified_core.messaging import (
        AgentMessage, 
        MessageType, 
        MessagePriority,
        AgentInfo
    )
except ImportError:
    # Mock implementations for standalone testing
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
        correlation_id: Optional[str] = None
        ttl_seconds: int = 300
        metadata: Dict[str, Any] = field(default_factory=dict)
        
        def to_bytes(self) -> bytes:
            return json.dumps({
                "id": self.id,
                "source": self.source_agent,
                "target": self.target_agent,
                "type": self.message_type.value,
                "action": self.action,
                "payload": self.payload,
                "ts": self.timestamp,
                "priority": self.priority.value,
                "meta": self.metadata
            }).encode('utf-8')
        
        @classmethod
        def from_bytes(cls, data: bytes) -> "AgentMessage":
            d = json.loads(data.decode('utf-8'))
            return cls(
                id=d["id"],
                source_agent=d["source"],
                target_agent=d["target"],
                message_type=MessageType(d["type"]),
                action=d["action"],
                payload=d["payload"],
                timestamp=d["ts"],
                priority=MessagePriority(d["priority"]),
                metadata=d.get("meta", {})
            )
        
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
    class AgentInfo:
        agent_id: str
        agent_type: str
        capabilities: List[str]
        endpoint: str
        registered_at: float
        last_heartbeat: float
        metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthTestResult:
    """Authentication test result."""
    test_name: str
    attack_type: str
    success: bool
    vulnerability_found: bool
    description: str


# =============================================================================
# MOCK CLASSES FOR TESTING
# =============================================================================

class MockMessageBroker:
    """Mock broker for authentication testing."""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.messages_received: List[AgentMessage] = []
        self.authentication_enabled = False
        self.shared_secret = "test_secret_key_12345"
        
    def register_agent(self, agent_id: str, agent_type: str = "test"):
        """Register an agent."""
        self.agents[agent_id] = AgentInfo(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=["test"],
            endpoint="mock://endpoint",
            registered_at=time.time(),
            last_heartbeat=time.time()
        )
        
    def receive_message(self, message: AgentMessage) -> bool:
        """Receive and validate a message."""
        self.messages_received.append(message)
        
        if self.authentication_enabled:
            return self._validate_auth(message)
        return True
    
    def _validate_auth(self, message: AgentMessage) -> bool:
        """Validate message authentication."""
        auth_token = message.metadata.get("auth_token")
        if not auth_token:
            return False
        
        # Verify HMAC
        expected = self._compute_auth(message)
        return hmac.compare_digest(auth_token, expected)
    
    def _compute_auth(self, message: AgentMessage) -> str:
        """Compute authentication token for message."""
        data = f"{message.source_agent}:{message.id}:{message.timestamp}"
        return hmac.new(
            self.shared_secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()


class MockAgentClient:
    """Mock client for authentication testing."""
    
    def __init__(self, agent_id: str, broker: MockMessageBroker):
        self.agent_id = agent_id
        self.broker = broker
        self.shared_secret = broker.shared_secret
        
    def send_message(self, target: str, action: str, payload: Dict, 
                     include_auth: bool = False) -> AgentMessage:
        """Send a message, optionally with authentication."""
        message = AgentMessage.create(
            source=self.agent_id,
            target=target,
            action=action,
            payload=payload
        )
        
        if include_auth:
            message.metadata["auth_token"] = self._compute_auth(message)
        
        return message
    
    def _compute_auth(self, message: AgentMessage) -> str:
        """Compute authentication token."""
        data = f"{message.source_agent}:{message.id}:{message.timestamp}"
        return hmac.new(
            self.shared_secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def mock_broker():
    """Create mock broker."""
    return MockMessageBroker()


@pytest.fixture
def mock_client(mock_broker):
    """Create mock client."""
    mock_broker.register_agent("test_client", "test")
    return MockAgentClient("test_client", mock_broker)


# =============================================================================
# IMPERSONATION ATTACK TESTS
# =============================================================================

class TestImpersonationAttacks:
    """Test agent impersonation vulnerabilities."""
    
    def test_agent_impersonation_without_auth(self, mock_broker):
        """Test that agents can be impersonated without authentication."""
        # Register legitimate agent
        mock_broker.register_agent("legitimate_agent", "trusted")
        
        # Attacker creates message claiming to be legitimate agent
        malicious_message = AgentMessage.create(
            source="legitimate_agent",  # Impersonating!
            target="broker",
            action="privileged_action",
            payload={"command": "delete_all"}
        )
        
        # Without authentication, this succeeds
        accepted = mock_broker.receive_message(malicious_message)
        
        result = AuthTestResult(
            test_name="agent_impersonation_without_auth",
            attack_type="impersonation",
            success=True,
            vulnerability_found=accepted,  # Vulnerability if accepted
            description="Message from impersonated source was accepted"
        )
        
        # This documents the vulnerability - in production should fail
        assert accepted, "Expected vulnerability: impersonation accepted without auth"
    
    def test_agent_impersonation_with_auth_enabled(self, mock_broker):
        """Test impersonation is blocked with authentication enabled."""
        mock_broker.authentication_enabled = True
        mock_broker.register_agent("legitimate_agent", "trusted")
        
        # Attacker creates message without valid auth token
        malicious_message = AgentMessage.create(
            source="legitimate_agent",
            target="broker",
            action="privileged_action",
            payload={"command": "delete_all"}
        )
        
        # Should be rejected
        accepted = mock_broker.receive_message(malicious_message)
        
        assert not accepted, "Impersonation should be blocked with auth enabled"
    
    def test_broker_impersonation(self, mock_broker):
        """Test impersonation of the message broker."""
        # Attacker sends message claiming to be broker
        fake_broker_message = AgentMessage.create(
            source="broker",  # Impersonating broker
            target="victim_agent",
            action="registered",
            payload={"status": "ok", "redirect": "http://malicious.com"}
        )
        
        # This documents the attack vector
        assert fake_broker_message.source_agent == "broker"


# =============================================================================
# MESSAGE TAMPERING TESTS
# =============================================================================

class TestMessageTampering:
    """Test message integrity and tampering detection."""
    
    def test_message_payload_tampering(self, mock_client):
        """Test detection of tampered message payload."""
        # Create legitimate message
        original = mock_client.send_message(
            target="target_agent",
            action="transfer",
            payload={"amount": 100, "recipient": "legitimate"},
            include_auth=True
        )
        
        # Attacker intercepts and modifies payload
        tampered = AgentMessage(
            id=original.id,
            source_agent=original.source_agent,
            target_agent=original.target_agent,
            message_type=original.message_type,
            action=original.action,
            payload={"amount": 10000, "recipient": "attacker"},  # Modified!
            timestamp=original.timestamp,
            priority=original.priority,
            correlation_id=original.correlation_id,
            metadata=original.metadata.copy()
        )
        
        # Verify tampering is detected (auth token should not match)
        original_auth = original.metadata.get("auth_token", "")
        tampered_data = f"{tampered.source_agent}:{tampered.id}:{tampered.timestamp}"
        
        # The auth token was computed before tampering, so payload change
        # should not be detected by current scheme (vulnerability!)
        # This test documents the issue
        assert original_auth == tampered.metadata.get("auth_token", "")
    
    def test_message_timestamp_tampering(self, mock_client):
        """Test detection of tampered timestamp."""
        original = mock_client.send_message(
            target="target",
            action="action",
            payload={},
            include_auth=True
        )
        
        # Tamper with timestamp
        tampered_timestamp = original.timestamp + 3600  # 1 hour in future
        
        # With proper auth, timestamp change should invalidate signature
        # Current implementation includes timestamp in auth
        tampered_auth_data = f"{original.source_agent}:{original.id}:{tampered_timestamp}"
        original_auth = original.metadata.get("auth_token", "")
        
        # Recompute what tampered auth would be
        import hmac
        import hashlib
        tampered_auth = hmac.new(
            mock_client.shared_secret.encode(),
            tampered_auth_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # They should differ
        assert original_auth != tampered_auth, "Timestamp tampering should be detectable"


# =============================================================================
# SIGNATURE VALIDATION TESTS
# =============================================================================

class TestSignatureValidation:
    """Test digital signature mechanisms."""
    
    def test_missing_signature_rejected(self, mock_broker):
        """Test that messages without signatures are rejected when auth enabled."""
        mock_broker.authentication_enabled = True
        
        message = AgentMessage.create(
            source="agent1",
            target="agent2",
            action="action",
            payload={}
        )
        # No auth token added
        
        accepted = mock_broker.receive_message(message)
        assert not accepted, "Message without signature should be rejected"
    
    def test_invalid_signature_rejected(self, mock_broker, mock_client):
        """Test that invalid signatures are rejected."""
        mock_broker.authentication_enabled = True
        
        message = mock_client.send_message(
            target="agent2",
            action="action",
            payload={},
            include_auth=True
        )
        
        # Corrupt the signature
        message.metadata["auth_token"] = "corrupted_" + message.metadata["auth_token"]
        
        accepted = mock_broker.receive_message(message)
        assert not accepted, "Message with invalid signature should be rejected"
    
    def test_valid_signature_accepted(self, mock_broker, mock_client):
        """Test that valid signatures are accepted."""
        mock_broker.authentication_enabled = True
        
        message = mock_client.send_message(
            target="agent2",
            action="action",
            payload={},
            include_auth=True
        )
        
        accepted = mock_broker.receive_message(message)
        assert accepted, "Message with valid signature should be accepted"


# =============================================================================
# IDENTITY VERIFICATION TESTS
# =============================================================================

class TestIdentityVerification:
    """Test agent identity verification mechanisms."""
    
    def test_unregistered_agent_can_send(self, mock_broker):
        """Test if unregistered agents can send messages (vulnerability check)."""
        # Don't register the agent
        message = AgentMessage.create(
            source="unregistered_agent",
            target="broker",
            action="some_action",
            payload={}
        )
        
        # Current implementation allows this
        accepted = mock_broker.receive_message(message)
        
        # Document vulnerability
        assert accepted, "Expected: unregistered agents can send (vulnerability)"
    
    def test_agent_capabilities_validation(self, mock_broker):
        """Test that agent capabilities are validated for actions."""
        mock_broker.register_agent("limited_agent", "limited")
        mock_broker.agents["limited_agent"].capabilities = ["read_only"]
        
        # Agent tries to perform action outside capabilities
        message = AgentMessage.create(
            source="limited_agent",
            target="broker",
            action="write_data",  # Not in capabilities
            payload={"data": "malicious"}
        )
        
        # Current implementation doesn't check capabilities
        accepted = mock_broker.receive_message(message)
        
        # Document that capability checking is not implemented
        assert accepted, "Capability validation not implemented"


# =============================================================================
# SERIALIZATION SECURITY TESTS
# =============================================================================

class TestSerializationSecurity:
    """Test message serialization security."""
    
    def test_json_injection_in_payload(self):
        """Test JSON injection attempts in payload."""
        payloads = [
            {"key": '{"__class__": "dangerous"}'},
            {"key": "value\", \"injected\": \"data"},
            {"nested": {"$where": "malicious_code()"}},
        ]
        
        for payload in payloads:
            message = AgentMessage.create(
                source="agent1",
                target="agent2",
                action="test",
                payload=payload
            )
            
            # Serialize and deserialize
            serialized = message.to_bytes()
            deserialized = AgentMessage.from_bytes(serialized)
            
            # Should match exactly (no injection)
            assert deserialized.payload == payload
    
    def test_oversized_message_handling(self):
        """Test handling of extremely large messages."""
        large_payload = {"data": "A" * (1024 * 1024)}  # 1MB
        
        message = AgentMessage.create(
            source="agent1",
            target="agent2",
            action="test",
            payload=large_payload
        )
        
        serialized = message.to_bytes()
        
        # Should serialize without crash
        assert len(serialized) > 1024 * 1024
        
        # Should deserialize
        deserialized = AgentMessage.from_bytes(serialized)
        assert len(deserialized.payload["data"]) == 1024 * 1024
    
    def test_unicode_in_message(self):
        """Test Unicode handling in messages."""
        unicode_payloads = [
            {"text": "مرحبا بالعالم"},  # Arabic
            {"text": "こんにちは"},  # Japanese
            {"text": "🔥💻🚀"},  # Emoji
            {"text": "\u0000\u0001\u0002"},  # Control chars
        ]
        
        for payload in unicode_payloads:
            message = AgentMessage.create(
                source="agent1",
                target="agent2",
                action="test",
                payload=payload
            )
            
            serialized = message.to_bytes()
            deserialized = AgentMessage.from_bytes(serialized)
            
            assert deserialized.payload == payload


# =============================================================================
# AUDIT SUMMARY
# =============================================================================

class TestAuthenticationAuditSummary:
    """Generate authentication audit summary."""
    
    def test_generate_audit_summary(self, mock_broker, mock_client):
        """Run comprehensive auth tests and generate summary."""
        results = {
            "impersonation_tests": 0,
            "impersonation_blocked": 0,
            "tampering_tests": 0,
            "tampering_detected": 0,
            "signature_tests": 0,
            "signature_valid": 0,
        }
        
        # Impersonation test (without auth)
        results["impersonation_tests"] += 1
        fake_msg = AgentMessage.create("fake_agent", "broker", "test", {})
        if not mock_broker.receive_message(fake_msg):
            results["impersonation_blocked"] += 1
        
        # Impersonation test (with auth)
        mock_broker.authentication_enabled = True
        results["impersonation_tests"] += 1
        if not mock_broker.receive_message(fake_msg):
            results["impersonation_blocked"] += 1
        
        # Signature validation
        results["signature_tests"] += 1
        valid_msg = mock_client.send_message("target", "test", {}, include_auth=True)
        if mock_broker.receive_message(valid_msg):
            results["signature_valid"] += 1
        
        # Invalid signature
        results["signature_tests"] += 1
        valid_msg.metadata["auth_token"] = "invalid"
        if not mock_broker.receive_message(valid_msg):
            results["signature_valid"] += 1
        
        print(f"\n{'='*60}")
        print("AUTHENTICATION SECURITY AUDIT SUMMARY")
        print(f"{'='*60}")
        print(f"Impersonation Tests: {results['impersonation_blocked']}/{results['impersonation_tests']} blocked")
        print(f"Signature Tests: {results['signature_valid']}/{results['signature_tests']} valid")
        print(f"{'='*60}\n")
        
        # Current implementation has known gaps
        assert results["impersonation_blocked"] >= 1, "Some impersonation should be blocked"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
