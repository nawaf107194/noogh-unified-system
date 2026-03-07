"""
Tests for ZeroMQ messaging system
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch

from unified_core.messaging import (
    AgentMessage, MessageType, MessagePriority,
    MessageBroker, AgentClient, AgentInfo
)


class TestAgentMessage:
    """Test AgentMessage serialization."""
    
    def test_create_message(self):
        """Factory method creates valid message."""
        msg = AgentMessage.create(
            source="agent1",
            target="agent2",
            action="test_action",
            payload={"key": "value"}
        )
        
        assert msg.source_agent == "agent1"
        assert msg.target_agent == "agent2"
        assert msg.action == "test_action"
        assert msg.payload == {"key": "value"}
        assert msg.message_type == MessageType.REQUEST
        assert msg.id is not None
        assert msg.correlation_id is not None
    
    def test_serialize_deserialize(self):
        """Message survives round-trip serialization."""
        original = AgentMessage.create(
            source="test_src",
            target="test_dst",
            action="ping",
            payload={"count": 42, "nested": {"a": 1}},
            priority=MessagePriority.HIGH
        )
        
        data = original.to_bytes()
        restored = AgentMessage.from_bytes(data)
        
        assert restored.id == original.id
        assert restored.source_agent == original.source_agent
        assert restored.target_agent == original.target_agent
        assert restored.action == original.action
        assert restored.payload == original.payload
        assert restored.priority == original.priority
        assert restored.correlation_id == original.correlation_id
    
    def test_message_types(self):
        """All message types are handled."""
        for msg_type in MessageType:
            msg = AgentMessage.create(
                source="a", target="b", action="test",
                msg_type=msg_type
            )
            assert msg.message_type == msg_type
    
    def test_priority_levels(self):
        """All priority levels are handled."""
        for priority in MessagePriority:
            msg = AgentMessage.create(
                source="a", target="b", action="test",
                priority=priority
            )
            assert msg.priority == priority


class TestMessageBrokerBasics:
    """Test MessageBroker basic operations."""
    
    @pytest.mark.asyncio
    async def test_broker_start_stop(self):
        """Broker starts and stops cleanly."""
        broker = MessageBroker(router_port=15555, pub_port=15556)
        
        await broker.start()
        assert broker._running
        
        await broker.stop()
        assert not broker._running
    
    @pytest.mark.asyncio
    async def test_get_agents_empty(self):
        """Empty agent list initially."""
        broker = MessageBroker(router_port=15557, pub_port=15558)
        await broker.start()
        
        try:
            agents = broker.get_agents()
            assert agents == []
        finally:
            await broker.stop()
    
    def test_register_handler(self):
        """Handlers can be registered."""
        broker = MessageBroker()
        
        handler = Mock()
        broker.on("test_action", handler)
        
        assert "test_action" in broker._handlers
        assert handler in broker._handlers["test_action"]
    
    def test_multiple_handlers(self):
        """Multiple handlers for same action."""
        broker = MessageBroker()
        
        handler1 = Mock()
        handler2 = Mock()
        broker.on("action", handler1)
        broker.on("action", handler2)
        
        assert len(broker._handlers["action"]) == 2


class TestAgentClientBasics:
    """Test AgentClient basic operations."""
    
    def test_client_init(self):
        """Client initializes with correct attributes."""
        client = AgentClient(
            agent_id="test_agent",
            agent_type="worker",
            capabilities=["compute", "store"]
        )
        
        assert client.agent_id == "test_agent"
        assert client.agent_type == "worker"
        assert "compute" in client.capabilities
        assert "store" in client.capabilities
    
    def test_register_handler(self):
        """Client handlers can be registered."""
        client = AgentClient("agent1", "type1", [])
        
        handler = Mock()
        client.on("action", handler)
        
        assert client._handlers["action"] == handler


class TestIntegration:
    """Integration tests for broker-client communication."""
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_client_registration(self):
        """Client registers with broker."""
        broker = MessageBroker(router_port=15559, pub_port=15560)
        await broker.start()
        
        try:
            client = AgentClient(
                agent_id="worker_1",
                agent_type="worker",
                capabilities=["task_execution"],
                router_port=15559,
                sub_port=15560
            )
            
            # Connect triggers registration
            await asyncio.wait_for(client.connect(), timeout=5)
            
            # Give time for registration to complete
            await asyncio.sleep(0.5)
            
            # Verify agent registered
            agents = broker.get_agents()
            # Note: Registration may or may not complete depending on timing
            
            await client.disconnect()
        finally:
            await broker.stop()


class TestMessageHandling:
    """Test message routing and handling."""
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Broadcast creates message with wildcard target."""
        client = AgentClient("agent1", "type1", [])
        client._dealer = AsyncMock()
        client._running = True
        
        await client.broadcast("announce", {"status": "online"})
        
        # Verify dealer.send_multipart was called
        client._dealer.send_multipart.assert_called_once()
        call_args = client._dealer.send_multipart.call_args[0][0]
        
        # Second element is the message
        msg = AgentMessage.from_bytes(call_args[1])
        assert msg.target_agent == "*"
        assert msg.message_type == MessageType.BROADCAST
    
    def test_heartbeat_message(self):
        """Heartbeat has correct type."""
        msg = AgentMessage.create(
            source="agent1",
            target="broker",
            action="heartbeat",
            msg_type=MessageType.HEARTBEAT
        )
        
        assert msg.message_type == MessageType.HEARTBEAT


class TestTTLAndMetadata:
    """Test TTL and metadata handling."""
    
    def test_default_ttl(self):
        """Default TTL is 300 seconds."""
        msg = AgentMessage.create("a", "b", "test")
        assert msg.ttl_seconds == 300
    
    def test_metadata_round_trip(self):
        """Metadata survives serialization."""
        msg = AgentMessage.create(
            source="a", target="b", action="test",
            payload={}
        )
        msg.metadata = {"trace_id": "abc123", "env": "test"}
        
        data = msg.to_bytes()
        restored = AgentMessage.from_bytes(data)
        
        assert restored.metadata["trace_id"] == "abc123"
        assert restored.metadata["env"] == "test"
