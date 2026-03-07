"""
ZeroMQ-based Inter-Agent Communication Protocol
High-performance async messaging between agents
"""
import asyncio
import logging
import json
import uuid
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import hashlib

try:
    import zmq
    import zmq.asyncio
except ImportError:
    zmq = None  # Optional dependency — messaging features disabled

logger = logging.getLogger("unified_core.agents.messaging")


class MessagePriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


@dataclass
class AgentMessage:
    """Standard message format for inter-agent communication."""
    id: str
    source_agent: str
    target_agent: str  # "*" for broadcast
    message_type: MessageType
    action: str
    payload: Dict[str, Any]
    timestamp: float
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None  # For request-response matching
    ttl_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes for transmission."""
        data = {
            "id": self.id,
            "source": self.source_agent,
            "target": self.target_agent,
            "type": self.message_type.value,
            "action": self.action,
            "payload": self.payload,
            "ts": self.timestamp,
            "priority": self.priority.value,
            "corr_id": self.correlation_id,
            "ttl": self.ttl_seconds,
            "meta": self.metadata
        }
        return json.dumps(data).encode('utf-8')
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "AgentMessage":
        """Deserialize from bytes."""
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
            correlation_id=d.get("corr_id"),
            ttl_seconds=d.get("ttl", 300),
            metadata=d.get("meta", {})
        )
    
    @staticmethod
    def create(
        source: str,
        target: str,
        action: str,
        payload: Dict = None,
        msg_type: MessageType = MessageType.REQUEST,
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: str = None
    ) -> "AgentMessage":
        """Factory method for creating messages."""
        import time
        return AgentMessage(
            id=str(uuid.uuid4()),
            source_agent=source,
            target_agent=target,
            message_type=msg_type,
            action=action,
            payload=payload or {},
            timestamp=time.time(),
            priority=priority,
            correlation_id=correlation_id or str(uuid.uuid4())
        )


@dataclass
class AgentInfo:
    """Registered agent information."""
    agent_id: str
    agent_type: str
    capabilities: List[str]
    endpoint: str
    registered_at: float
    last_heartbeat: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class MessageBroker:
    """
    Central message broker for agent communication.
    Uses ZeroMQ for high-performance async messaging.
    
    Architecture:
    - ROUTER socket for point-to-point messaging
    - PUB socket for broadcast/events
    - Async event loop for non-blocking ops
    """
    
    def __init__(
        self,
        router_port: int = 5555,
        pub_port: int = 5556,
        heartbeat_interval: int = 30
    ):
        self.router_port = router_port
        self.pub_port = pub_port
        self.heartbeat_interval = heartbeat_interval
        
        self._context: Optional[zmq.asyncio.Context] = None
        self._router: Optional[zmq.asyncio.Socket] = None
        self._publisher: Optional[zmq.asyncio.Socket] = None
        
        self._agents: Dict[str, AgentInfo] = {}
        self._handlers: Dict[str, List[Callable]] = {}
        self._pending_responses: Dict[str, asyncio.Future] = {}
        
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    async def start(self):
        """Start the message broker."""
        self._context = zmq.asyncio.Context()
        
        # ROUTER for req-rep pattern
        self._router = self._context.socket(zmq.ROUTER)
        self._router.bind(f"tcp://*:{self.router_port}")
        
        # PUB for broadcast
        self._publisher = self._context.socket(zmq.PUB)
        self._publisher.bind(f"tcp://*:{self.pub_port}")
        
        self._running = True
        
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._message_loop()),
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]
        
        logger.info(f"MessageBroker started on ports {self.router_port}/{self.pub_port}")
    
    async def stop(self):
        """Stop the message broker."""
        self._running = False
        
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        if self._router:
            self._router.close()
        if self._publisher:
            self._publisher.close()
        if self._context:
            self._context.term()
        
        logger.info("MessageBroker stopped")
    
    async def _message_loop(self):
        """Main message processing loop."""
        while self._running:
            try:
                # ROUTER receives [identity, empty, message]
                frames = await asyncio.wait_for(
                    self._router.recv_multipart(),
                    timeout=1.0
                )
                
                if len(frames) >= 3:
                    identity = frames[0]
                    message_data = frames[-1]
                    
                    try:
                        message = AgentMessage.from_bytes(message_data)
                        await self._handle_message(identity, message)
                    except Exception as e:
                        logger.error(f"Message parse error: {e}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Message loop error: {e}")
    
    async def _handle_message(self, identity: bytes, message: AgentMessage):
        """Process incoming message."""
        logger.debug(f"Received: {message.action} from {message.source_agent}")
        
        # Handle registration
        if message.action == "register":
            await self._handle_registration(identity, message)
            return
        
        # Handle heartbeat
        if message.message_type == MessageType.HEARTBEAT:
            await self._handle_heartbeat(message)
            return
        
        # Handle response to pending request
        if message.message_type == MessageType.RESPONSE and message.correlation_id:
            if message.correlation_id in self._pending_responses:
                self._pending_responses[message.correlation_id].set_result(message)
                del self._pending_responses[message.correlation_id]
                return
        
        # Route to target agent
        if message.target_agent == "*":
            # Broadcast
            await self._broadcast(message)
        elif message.target_agent in self._agents:
            await self._route_to_agent(message)
        
        # Trigger handlers
        await self._trigger_handlers(message)
    
    async def _handle_registration(self, identity: bytes, message: AgentMessage):
        """Handle agent registration."""
        import time
        
        payload = message.payload
        agent_info = AgentInfo(
            agent_id=message.source_agent,
            agent_type=payload.get("type", "generic"),
            capabilities=payload.get("capabilities", []),
            endpoint=identity.hex(),
            registered_at=time.time(),
            last_heartbeat=time.time(),
            metadata=payload.get("metadata", {})
        )
        
        self._agents[message.source_agent] = agent_info
        logger.info(f"Agent registered: {message.source_agent} ({agent_info.agent_type})")
        
        # Send confirmation
        response = AgentMessage.create(
            source="broker",
            target=message.source_agent,
            action="registered",
            payload={"status": "ok", "agent_count": len(self._agents)},
            msg_type=MessageType.RESPONSE,
            correlation_id=message.correlation_id
        )
        await self._send_direct(identity, response)
    
    async def _handle_heartbeat(self, message: AgentMessage):
        """Update agent heartbeat timestamp."""
        import time
        if message.source_agent in self._agents:
            self._agents[message.source_agent].last_heartbeat = time.time()
    
    async def _route_to_agent(self, message: AgentMessage):
        """Route message to specific agent."""
        agent = self._agents.get(message.target_agent)
        if not agent:
            logger.warning(f"Target agent not found: {message.target_agent}")
            return
        
        identity = bytes.fromhex(agent.endpoint)
        await self._send_direct(identity, message)
    
    async def _send_direct(self, identity: bytes, message: AgentMessage):
        """Send message directly to an agent."""
        await self._router.send_multipart([
            identity,
            b"",
            message.to_bytes()
        ])
    
    async def _broadcast(self, message: AgentMessage):
        """Broadcast message to all agents via PUB socket."""
        topic = message.action.encode('utf-8')
        await self._publisher.send_multipart([topic, message.to_bytes()])
    
    async def _trigger_handlers(self, message: AgentMessage):
        """Trigger registered handlers for message action."""
        handlers = self._handlers.get(message.action, [])
        handlers.extend(self._handlers.get("*", []))  # Wildcard handlers
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Handler error for {message.action}: {e}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat checks."""
        while self._running:
            await asyncio.sleep(self.heartbeat_interval)
            # Optionally send heartbeat requests to all agents
    
    async def _cleanup_loop(self):
        """Clean up stale agents and expired messages."""
        import time
        while self._running:
            await asyncio.sleep(60)
            
            now = time.time()
            stale_threshold = now - (self.heartbeat_interval * 3)
            
            stale_agents = [
                aid for aid, info in self._agents.items()
                if info.last_heartbeat < stale_threshold
            ]
            
            for aid in stale_agents:
                logger.warning(f"Removing stale agent: {aid}")
                del self._agents[aid]
    
    def on(self, action: str, handler: Callable):
        """Register handler for specific action."""
        if action not in self._handlers:
            self._handlers[action] = []
        self._handlers[action].append(handler)
    
    def get_agents(self, agent_type: Optional[str] = None) -> List[AgentInfo]:
        """Get list of registered agents."""
        agents = list(self._agents.values())
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
        return agents
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get specific agent info."""
        return self._agents.get(agent_id)


class AgentClient:
    """
    Client for agents to communicate via the broker.
    Handles connection, registration, and message sending/receiving.
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[str],
        broker_host: str = "localhost",
        router_port: int = 5555,
        sub_port: int = 5556
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.broker_host = broker_host
        self.router_port = router_port
        self.sub_port = sub_port
        
        self._context: Optional[zmq.asyncio.Context] = None
        self._dealer: Optional[zmq.asyncio.Socket] = None
        self._subscriber: Optional[zmq.asyncio.Socket] = None
        
        self._handlers: Dict[str, Callable] = {}
        self._pending: Dict[str, asyncio.Future] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    async def connect(self):
        """Connect to message broker."""
        self._context = zmq.asyncio.Context()
        
        # DEALER for req-rep
        self._dealer = self._context.socket(zmq.DEALER)
        self._dealer.setsockopt(zmq.IDENTITY, self.agent_id.encode('utf-8'))
        self._dealer.connect(f"tcp://{self.broker_host}:{self.router_port}")
        
        # SUB for broadcasts
        self._subscriber = self._context.socket(zmq.SUB)
        self._subscriber.connect(f"tcp://{self.broker_host}:{self.sub_port}")
        self._subscriber.setsockopt_string(zmq.SUBSCRIBE, "")  # All topics
        
        self._running = True
        
        # Register with broker
        await self._register()
        
        # Start message loops
        self._tasks = [
            asyncio.create_task(self._dealer_loop()),
            asyncio.create_task(self._sub_loop()),
            asyncio.create_task(self._heartbeat_loop())
        ]
        
        logger.info(f"Agent {self.agent_id} connected to broker")
    
    async def disconnect(self):
        """Disconnect from broker."""
        self._running = False
        
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        if self._dealer:
            self._dealer.close()
        if self._subscriber:
            self._subscriber.close()
        if self._context:
            self._context.term()
    
    async def _register(self):
        """Register with the message broker."""
        message = AgentMessage.create(
            source=self.agent_id,
            target="broker",
            action="register",
            payload={
                "type": self.agent_type,
                "capabilities": self.capabilities
            }
        )
        
        response = await self.request("broker", "register", message.payload, timeout=5.0)
        if response and response.payload.get("status") == "ok":
            logger.info(f"Agent {self.agent_id} registered successfully")
        else:
            logger.error(f"Agent registration failed")
    
    async def _dealer_loop(self):
        """Handle incoming DEALER messages."""
        while self._running:
            try:
                frames = await asyncio.wait_for(
                    self._dealer.recv_multipart(),
                    timeout=1.0
                )
                
                if frames:
                    message = AgentMessage.from_bytes(frames[-1])
                    await self._handle_message(message)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Dealer loop error: {e}")
    
    async def _sub_loop(self):
        """Handle broadcast messages."""
        while self._running:
            try:
                frames = await asyncio.wait_for(
                    self._subscriber.recv_multipart(),
                    timeout=1.0
                )
                
                if len(frames) >= 2:
                    message = AgentMessage.from_bytes(frames[1])
                    await self._handle_message(message)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Sub loop error: {e}")
    
    async def _handle_message(self, message: AgentMessage):
        """Process incoming message."""
        # Check if response to pending request
        if message.correlation_id in self._pending:
            self._pending[message.correlation_id].set_result(message)
            return
        
        # Trigger handler
        handler = self._handlers.get(message.action)
        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(message)
                else:
                    result = handler(message)
                
                # Send response if handler returns data
                if result is not None and message.message_type == MessageType.REQUEST:
                    await self.respond(message, result)
            except Exception as e:
                logger.error(f"Handler error: {e}")
                await self.respond(message, {"error": str(e)}, is_error=True)
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self._running:
            await asyncio.sleep(30)
            await self.send("broker", "heartbeat", {}, msg_type=MessageType.HEARTBEAT)
    
    def on(self, action: str, handler: Callable):
        """Register handler for action."""
        self._handlers[action] = handler
    
    async def send(
        self,
        target: str,
        action: str,
        payload: Dict,
        msg_type: MessageType = MessageType.EVENT,
        priority: MessagePriority = MessagePriority.NORMAL
    ):
        """Send message without waiting for response."""
        message = AgentMessage.create(
            source=self.agent_id,
            target=target,
            action=action,
            payload=payload,
            msg_type=msg_type,
            priority=priority
        )
        
        await self._dealer.send_multipart([b"", message.to_bytes()])
    
    async def request(
        self,
        target: str,
        action: str,
        payload: Dict,
        timeout: float = 30.0,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Optional[AgentMessage]:
        """Send request and wait for response."""
        message = AgentMessage.create(
            source=self.agent_id,
            target=target,
            action=action,
            payload=payload,
            msg_type=MessageType.REQUEST,
            priority=priority
        )
        
        # Create future for response
        future = asyncio.get_event_loop().create_future()
        self._pending[message.correlation_id] = future
        
        try:
            await self._dealer.send_multipart([b"", message.to_bytes()])
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout: {action} -> {target}")
            return None
        finally:
            self._pending.pop(message.correlation_id, None)
    
    async def respond(
        self,
        original: AgentMessage,
        payload: Dict,
        is_error: bool = False
    ):
        """Send response to a request."""
        response = AgentMessage.create(
            source=self.agent_id,
            target=original.source_agent,
            action=f"{original.action}_response",
            payload=payload,
            msg_type=MessageType.ERROR if is_error else MessageType.RESPONSE,
            correlation_id=original.correlation_id
        )
        
        await self._dealer.send_multipart([b"", response.to_bytes()])
    
    async def broadcast(self, action: str, payload: Dict):
        """Broadcast message to all agents."""
        await self.send("*", action, payload, msg_type=MessageType.BROADCAST)
