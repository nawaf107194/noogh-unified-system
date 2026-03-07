import pytest

from unified_core.main import UnifiedCore
from unified_core.configs import Config, PostgresConfig, VectorDBConfig, GraphDBConfig, DataRouterConfig
from unified_core.managers import PostgresManager, VectorDBManager, GraphDBManager, DataRouter
from unified_core.brokers import MessageBroker
from unified_core.security import SecOpsAgent, DevAgent
from unified_core.monitors import ResourceMonitor, ProcessManager
from unified_core.filesystems import SecureFileSystem
from unified_core.hubs import MultimodalHub

def test_happy_path():
    config = Config(postgres=PostgresConfig(), vector_db=VectorDBConfig(), graph_db=GraphDBConfig(),
                     data_router=DataRouterConfig(), message_broker=None, secops=SecOpsAgent(),
                     dev_agent=DevAgent(), resource_monitor=ResourceMonitor(), process_manager=ProcessManager(),
                     filesystem=SecureFileSystem(), multimodal_hub=MultimodalHub())
    unified_core = UnifiedCore(config)
    assert unified_core.config == config
    assert isinstance(unified_core.postgres, PostgresManager)
    assert isinstance(unified_core.vector_db, VectorDBManager)
    assert isinstance(unified_core.graph_db, GraphDBManager)
    assert isinstance(unified_core.data_router, DataRouter)
    assert unified_core.message_broker is None
    assert isinstance(unified_core.secops, SecOpsAgent)
    assert isinstance(unified_core.dev_agent, DevAgent)
    assert isinstance(unified_core.resource_monitor, ResourceMonitor)
    assert isinstance(unified_core.process_manager, ProcessManager)
    assert isinstance(unified_core.filesystem, SecureFileSystem)
    assert isinstance(unified_core.multimodal_hub, MultimodalHub)
    assert not unified_core._running
    assert isinstance(unified_core._shutdown_event, asyncio.Event)

def test_edge_case_empty_config():
    config = {}
    unified_core = UnifiedCore(config)
    assert unified_core.config == {}
    assert unified_core.postgres is None
    assert unified_core.vector_db is None
    assert unified_core.graph_db is None
    assert unified_core.data_router is None
    assert unified_core.message_broker is None
    assert unified_core.secops is None
    assert unified_core.dev_agent is None
    assert unified_core.resource_monitor is None
    assert unified_core.process_manager is None
    assert unified_core.filesystem is None
    assert unified_core.multimodal_hub is None
    assert not unified_core._running
    assert isinstance(unified_core._shutdown_event, asyncio.Event)

def test_edge_case_none_config():
    config = None
    unified_core = UnifiedCore(config)
    assert unified_core.config == {}
    assert unified_core.postgres is None
    assert unified_core.vector_db is None
    assert unified_core.graph_db is None
    assert unified_core.data_router is None
    assert unified_core.message_broker is None
    assert unified_core.secops is None
    assert unified_core.dev_agent is None
    assert unified_core.resource_monitor is None
    assert unified_core.process_manager is None
    assert unified_core.filesystem is None
    assert unified_core.multimodal_hub is None
    assert not unified_core._running
    assert isinstance(unified_core._shutdown_event, asyncio.Event)

def test_error_case_invalid_config():
    config = Config(postgres='invalid', vector_db=VectorDBConfig(), graph_db=GraphDBConfig(),
                     data_router=DataRouterConfig(), message_broker=None, secops=SecOpsAgent(),
                     dev_agent=DevAgent(), resource_monitor=ResourceMonitor(), process_manager=ProcessManager(),
                     filesystem=SecureFileSystem(), multimodal_hub=MultimodalHub())
    with pytest.raises(ValueError):
        UnifiedCore(config)