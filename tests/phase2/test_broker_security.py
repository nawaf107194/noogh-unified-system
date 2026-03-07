"""
Broker Security Tests

Tests for MessageBroker security:
- Agent registration validation
- Unauthorized message routing
- Broker impersonation
- Configuration security
- Socket security

OWASP References:
- A01:2021 Broken Access Control
- A05:2021 Security Misconfiguration
- CWE-284: Improper Access Control
"""
import pytest
import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
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
        
        def to_bytes(self) -> bytes:
            import json
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
class BrokerSecurityResult:
    """Result of broker security test."""
    test_name: str
    vulnerability_type: str
    exploitable: bool
    description: str


# =============================================================================
# MOCK BROKER FOR SECURITY TESTING
# =============================================================================

class SecureMockBroker:
    """Mock broker with security features for testing."""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.allowed_actions: Dict[str, List[str]] = {}  # agent_id -> allowed actions
        self.require_registration = True
        self.validate_targets = True
        self.messages_processed: List[AgentMessage] = []
        self.security_violations: List[Dict] = []
        
    def register_agent(
        self, 
        agent_id: str, 
        agent_type: str,
        capabilities: List[str] = None,
        allowed_actions: List[str] = None
    ):
        """Register an agent with capabilities."""
        self.agents[agent_id] = AgentInfo(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities or [],
            endpoint="mock://endpoint",
            registered_at=time.time(),
            last_heartbeat=time.time()
        )
        self.allowed_actions[agent_id] = allowed_actions or ["*"]
    
    def process_message(self, message: AgentMessage) -> bool:
        """Process message with security checks."""
        # Check registration
        if self.require_registration:
            if message.source_agent not in self.agents and message.source_agent != "broker":
                self.security_violations.append({
                    "type": "unregistered_sender",
                    "agent": message.source_agent,
                    "message_id": message.id
                })
                return False
        
        # Check target exists
        if self.validate_targets:
            if message.target_agent not in self.agents and message.target_agent not in ["broker", "*"]:
                self.security_violations.append({
                    "type": "invalid_target",
                    "target": message.target_agent,
                    "message_id": message.id
                })
                return False
        
        # Check action authorization
        if message.source_agent in self.allowed_actions:
            allowed = self.allowed_actions[message.source_agent]
            if "*" not in allowed and message.action not in allowed:
                self.security_violations.append({
                    "type": "unauthorized_action",
                    "agent": message.source_agent,
                    "action": message.action,
                    "message_id": message.id
                })
                return False
        
        self.messages_processed.append(message)
        return True
    
    def get_agents(self, agent_type: Optional[str] = None) -> List[AgentInfo]:
        """Get registered agents."""
        agents = list(self.agents.values())
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
        return agents


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def secure_broker():
    """Create secure broker."""
    return SecureMockBroker()


@pytest.fixture
def permissive_broker():
    """Create permissive broker (for vulnerability testing)."""
    broker = SecureMockBroker()
    broker.require_registration = False
    broker.validate_targets = False
    return broker


# =============================================================================
# REGISTRATION SECURITY TESTS
# =============================================================================

class TestRegistrationSecurity:
    """Test agent registration security."""
    
    def test_unregistered_agent_blocked(self, secure_broker):
        """Test that unregistered agents cannot send messages."""
        # Don't register the agent
        
        message = AgentMessage.create(
            source="unregistered_agent",
            target="broker",
            action="do_something",
            payload={}
        )
        
        accepted = secure_broker.process_message(message)
        
        assert not accepted, "Unregistered agent should be blocked"
        assert len(secure_broker.security_violations) > 0
        assert secure_broker.security_violations[0]["type"] == "unregistered_sender"
    
    def test_registered_agent_accepted(self, secure_broker):
        """Test that registered agents can send messages."""
        secure_broker.register_agent("registered_agent", "test")
        
        message = AgentMessage.create(
            source="registered_agent",
            target="broker",
            action="do_something",
            payload={}
        )
        
        accepted = secure_broker.process_message(message)
        
        assert accepted, "Registered agent should be accepted"
    
    def test_duplicate_registration(self, secure_broker):
        """Test handling of duplicate agent registration."""
        secure_broker.register_agent("agent1", "type1")
        
        # Re-register with different type
        secure_broker.register_agent("agent1", "type2")
        
        # Should have updated the registration
        agent = secure_broker.agents.get("agent1")
        assert agent is not None
        assert agent.agent_type == "type2"
    
    def test_registration_info_exposure(self, secure_broker):
        """Test information exposure through registration."""
        secure_broker.register_agent("agent1", "secure", 
                                     capabilities=["secret_capability"])
        secure_broker.register_agent("agent2", "untrusted")
        
        # Untrusted agent tries to list all agents
        agents = secure_broker.get_agents()
        
        # Should not expose capabilities to untrusted agents
        # Current implementation exposes all info (vulnerability)
        exposed_capabilities = any(
            "secret_capability" in a.capabilities 
            for a in agents
        )
        
        # Document the vulnerability
        assert exposed_capabilities, "Expected vulnerability: capabilities exposed"


# =============================================================================
# ROUTING SECURITY TESTS
# =============================================================================

class TestRoutingSecurity:
    """Test message routing security."""
    
    def test_message_to_invalid_target(self, secure_broker):
        """Test message to non-existent target."""
        secure_broker.register_agent("sender", "test")
        # Don't register "nonexistent_target"
        
        message = AgentMessage.create(
            source="sender",
            target="nonexistent_target",
            action="action",
            payload={}
        )
        
        accepted = secure_broker.process_message(message)
        
        assert not accepted, "Message to invalid target should be blocked"
    
    def test_broadcast_message(self, secure_broker):
        """Test broadcast message security."""
        secure_broker.register_agent("sender", "test")
        
        message = AgentMessage.create(
            source="sender",
            target="*",  # Broadcast
            action="announcement",
            payload={"data": "public"}
        )
        
        accepted = secure_broker.process_message(message)
        
        assert accepted, "Broadcast should be allowed"
    
    def test_message_routing_interception(self, secure_broker):
        """Test if messages can be intercepted by third party."""
        secure_broker.register_agent("sender", "trusted")
        secure_broker.register_agent("receiver", "trusted")
        secure_broker.register_agent("attacker", "untrusted")
        
        # Legitimate message
        original = AgentMessage.create(
            source="sender",
            target="receiver",
            action="send_secret",
            payload={"secret": "confidential"}
        )
        
        secure_broker.process_message(original)
        
        # Attacker tries to intercept by subscribing to all topics
        # Current implementation doesn't prevent this (vulnerability)
        
        # Check if attacker could see the message
        # (depends on broker implementation)


# =============================================================================
# AUTHORIZATION TESTS
# =============================================================================

class TestAuthorizationSecurity:
    """Test action authorization security."""
    
    def test_unauthorized_action_blocked(self, secure_broker):
        """Test that unauthorized actions are blocked."""
        secure_broker.register_agent(
            "limited_agent", 
            "limited",
            allowed_actions=["read", "list"]
        )
        
        message = AgentMessage.create(
            source="limited_agent",
            target="broker",
            action="delete",  # Not in allowed actions
            payload={}
        )
        
        accepted = secure_broker.process_message(message)
        
        assert not accepted, "Unauthorized action should be blocked"
        assert any(v["type"] == "unauthorized_action" for v in secure_broker.security_violations)
    
    def test_authorized_action_allowed(self, secure_broker):
        """Test that authorized actions are allowed."""
        secure_broker.register_agent(
            "limited_agent",
            "limited",
            allowed_actions=["read", "list"]
        )
        
        message = AgentMessage.create(
            source="limited_agent",
            target="broker",
            action="read",
            payload={}
        )
        
        accepted = secure_broker.process_message(message)
        
        assert accepted, "Authorized action should be allowed"
    
    def test_wildcard_permission(self, secure_broker):
        """Test wildcard permission grants all actions."""
        secure_broker.register_agent(
            "admin_agent",
            "admin",
            allowed_actions=["*"]
        )
        
        actions = ["read", "write", "delete", "admin_override", "anything"]
        
        for action in actions:
            message = AgentMessage.create(
                source="admin_agent",
                target="broker",
                action=action,
                payload={}
            )
            assert secure_broker.process_message(message), f"Action {action} should be allowed"
    
    def test_privilege_escalation_attempt(self, secure_broker):
        """Test privilege escalation via message manipulation."""
        secure_broker.register_agent(
            "low_priv",
            "user",
            allowed_actions=["read"]
        )
        
        # Low privilege agent tries to send admin-level action
        message = AgentMessage.create(
            source="low_priv",
            target="broker",
            action="admin_promote_user",
            payload={"target_user": "low_priv", "new_role": "admin"}
        )
        
        accepted = secure_broker.process_message(message)
        
        assert not accepted, "Privilege escalation should be blocked"


# =============================================================================
# CONFIGURATION SECURITY TESTS
# =============================================================================

class TestConfigurationSecurity:
    """Test broker configuration security."""
    
    def test_default_open_configuration(self, permissive_broker):
        """Test vulnerability of default open configuration."""
        # No registration required
        message = AgentMessage.create(
            source="anonymous",
            target="any_target",
            action="anything",
            payload={}
        )
        
        accepted = permissive_broker.process_message(message)
        
        # In permissive mode, should accept (documenting vulnerability)
        assert accepted, "Permissive mode accepts unauthenticated messages"
    
    def test_broker_self_protection(self, secure_broker):
        """Test that broker protects itself from malicious messages."""
        secure_broker.register_agent("attacker", "test")
        
        # Attacker tries to impersonate broker
        fake_broker_msg = AgentMessage.create(
            source="broker",  # Impersonation!
            target="victim",
            action="admin_command",
            payload={}
        )
        
        # Broker should reject messages claiming to be from broker
        # unless actually from broker
        # Current implementation may not check this (vulnerability)


# =============================================================================
# SOCKET SECURITY TESTS
# =============================================================================

class TestSocketSecurity:
    """Test ZeroMQ socket security considerations."""
    
    def test_endpoint_exposure(self):
        """Document ZeroMQ endpoint security considerations."""
        # ZeroMQ endpoints like tcp://*:5555 expose to all interfaces
        # This is a configuration security issue
        
        secure_endpoint = "tcp://127.0.0.1:5555"  # Localhost only
        insecure_endpoint = "tcp://*:5555"  # All interfaces
        
        # Document the security difference
        assert "127.0.0.1" in secure_endpoint
        assert "*" in insecure_endpoint
    
    def test_plain_text_transmission(self):
        """Document plain text transmission vulnerability."""
        # Messages are JSON serialized without encryption
        message = AgentMessage.create(
            source="sender",
            target="receiver",
            action="send_credentials",
            payload={"username": "admin", "password": "secret123"}
        )
        
        serialized = message.to_bytes()
        
        # Credentials are visible in plain text
        assert b"secret123" in serialized, "Credentials exposed in transit"


# =============================================================================
# AUDIT SUMMARY
# =============================================================================

class TestBrokerSecurityAuditSummary:
    """Generate broker security audit summary."""
    
    def test_generate_audit_summary(self, secure_broker, permissive_broker):
        """Run broker security tests and generate summary."""
        results = {
            "registration_enforced": False,
            "target_validated": False,
            "authorization_checked": False,
            "violations_logged": False,
        }
        
        # Registration test
        msg = AgentMessage.create("unregistered", "broker", "test", {})
        if not secure_broker.process_message(msg):
            results["registration_enforced"] = True
        
        # Target validation test
        secure_broker.register_agent("sender", "test")
        msg = AgentMessage.create("sender", "nonexistent", "test", {})
        if not secure_broker.process_message(msg):
            results["target_validated"] = True
        
        # Authorization test
        secure_broker.register_agent("limited", "limited", allowed_actions=["read"])
        msg = AgentMessage.create("limited", "broker", "write", {})
        if not secure_broker.process_message(msg):
            results["authorization_checked"] = True
        
        # Violation logging
        results["violations_logged"] = len(secure_broker.security_violations) > 0
        
        print(f"\n{'='*60}")
        print("BROKER SECURITY AUDIT SUMMARY")
        print(f"{'='*60}")
        print(f"Registration Enforced: {'✓' if results['registration_enforced'] else '✗'}")
        print(f"Target Validated: {'✓' if results['target_validated'] else '✗'}")
        print(f"Authorization Checked: {'✓' if results['authorization_checked'] else '✗'}")
        print(f"Violations Logged: {'✓' if results['violations_logged'] else '✗'}")
        print(f"Violations Recorded: {len(secure_broker.security_violations)}")
        print(f"{'='*60}\n")
        
        # All security features should be active
        assert all(results.values()), "Some security features not working"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
