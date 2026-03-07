import pytest
from unittest.mock import patch
from typing import List, Callable, Optional, Dict

class MockAsyncioContext:
    def __init__(self):
        self.term_called = False
    
    async def term(self):
        self.term_called = True

class MockAsyncioSocket:
    def __init__(self):
        self.connect_called = False
        self.bind_called = False
        self.poll_called = False
        self.send_multipart_called = False
        self.recv_multipart_called = False
    
    async def connect(self, address):
        self.connect_called = True
    
    async def bind(self, address):
        self.bind_called = True
    
    async def poll(self, timeout=None):
        self.poll_called = True
    
    async def send_multipart(self, parts):
        self.send_multipart_called = True
    
    async def recv_multipart(self):
        self.recv_multipart_called = True

from unified_core.messaging import Messaging

@pytest.mark.asyncio
async def test_init_happy_path():
    agent_id = "test_agent"
    agent_type = "test_type"
    capabilities = ["cap1", "cap2"]
    messaging = Messaging(agent_id, agent_type, capabilities)
    
    assert messaging.agent_id == agent_id
    assert messaging.agent_type == agent_type
    assert messaging.capabilities == capabilities
    assert messaging.broker_host == "localhost"
    assert messaging.router_port == 5555
    assert messaging.sub_port == 5556
    
    assert messaging._context is None
    assert messaging._dealer is None
    assert messaging._subscriber is None
    
    assert messaging._handlers == {}
    assert messaging._pending == {}
    assert not messaging._running
    assert messaging._tasks == []

@pytest.mark.asyncio
async def test_init_edge_cases():
    agent_id = ""
    agent_type = "test_type"
    capabilities = []
    
    messaging = Messaging(agent_id, agent_type, capabilities)
    
    assert messaging.agent_id == ""
    assert messaging.agent_type == "test_type"
    assert messaging.capabilities == []
    assert messaging.broker_host == "localhost"
    assert messaging.router_port == 5555
    assert messaging.sub_port == 5556
    
    assert messaging._context is None
    assert messaging._dealer is None
    assert messaging._subscriber is None
    
    assert messaging._handlers == {}
    assert messaging._pending == {}
    assert not messaging._running
    assert messaging._tasks == []

@pytest.mark.asyncio
async def test_init_error_cases():
    agent_id = None
    agent_type = "test_type"
    capabilities = ["cap1", "cap2"]
    
    with pytest.raises(TypeError):
        Messaging(agent_id, agent_type, capabilities)

@pytest.mark.asyncio
@patch('unified_core.messaging.zmq.asyncio.Context', new_callable=MockAsyncioContext)
async def test_init_async_behavior(context_mock):
    agent_id = "test_agent"
    agent_type = "test_type"
    capabilities = ["cap1", "cap2"]
    
    messaging = Messaging(agent_id, agent_type, capabilities)
    
    assert context_mock.term_called == False