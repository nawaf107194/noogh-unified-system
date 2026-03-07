"""
The Unified Core - Main Entry Point
Initializes and orchestrates all system components
"""
import asyncio
import logging
import os
import signal
from typing import Dict, Optional

from unified_core.db import PostgresManager, VectorDBManager, GraphDBManager, DataRouter
from unified_core.messaging import MessageBroker, AgentClient
from unified_core.dev_agent import DevAgent
from unified_core.secops_agent import SecOpsAgent
from unified_core.resources.monitor import ResourceMonitor
from unified_core.resources.process_manager import ProcessManager
from unified_core.resources.filesystem import SecureFileSystem
from unified_core.multimodal import MultimodalHub, TextGenerator, ImageGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("unified_core.main")


class UnifiedCore:
    """
    The Unified Core - Central orchestrator for all subsystems.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        
        # Database Layer
        self.postgres: Optional[PostgresManager] = None
        self.vector_db: Optional[VectorDBManager] = None
        self.graph_db: Optional[GraphDBManager] = None
        self.data_router: Optional[DataRouter] = None
        
        # Communication Layer
        self.message_broker: Optional[MessageBroker] = None
        
        # Security Layer
        self.secops: Optional[SecOpsAgent] = None
        self.dev_agent: Optional[DevAgent] = None
        
        # Resource Layer
        self.resource_monitor: Optional[ResourceMonitor] = None
        self.process_manager: Optional[ProcessManager] = None
        self.filesystem: Optional[SecureFileSystem] = None
        
        # Neural Layer
        self.multimodal_hub: Optional[MultimodalHub] = None
        
        self._running = False
        self._shutdown_event = asyncio.Event()
    
    def _default_config(self) -> Dict:
        return {
            # Database
            "postgres_host": os.getenv("POSTGRES_HOST", "localhost"),
            "postgres_port": int(os.getenv("POSTGRES_PORT", 5432)),
            "postgres_db": os.getenv("POSTGRES_DB", "unified_core"),
            "postgres_user": os.getenv("POSTGRES_USER", "postgres"),
            "postgres_password": os.getenv("POSTGRES_PASSWORD", ""),
            
            "milvus_host": os.getenv("MILVUS_HOST", "localhost"),
            "milvus_port": int(os.getenv("MILVUS_PORT", 19530)),
            
            "neo4j_uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            "neo4j_user": os.getenv("NEO4J_USER", "neo4j"),
            "neo4j_password": os.getenv("NEO4J_PASSWORD", ""),
            
            # Messaging
            "broker_router_port": int(os.getenv("BROKER_ROUTER_PORT", 5555)),
            "broker_pub_port": int(os.getenv("BROKER_PUB_PORT", 5556)),
            
            # File System
            "allowed_roots": os.getenv("ALLOWED_ROOTS", "/app/data,/tmp").split(","),
            
            # Neural
            "llm_model": os.getenv("LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.1"),
            "gpu_enabled": os.getenv("GPU_ENABLED", "true").lower() == "true",
        }
    
    async def initialize(self) -> bool:
        """Initialize all subsystems (Refactored v3.5.6)."""
        logger.info("=" * 60)
        logger.info("THE UNIFIED CORE (MODULAR) - Initializing...")
        logger.info("=" * 60)
        
        success = True
        
        # Sequentially initialize specialized layers
        success &= await self._init_database_layer()
        success &= await self._init_comm_layer()
        success &= await self._init_security_layer()
        success &= await self._init_resource_layer()
        success &= await self._init_neural_layer()
        
        # Start background orchestration
        await self._start_background_services()
        
        self._running = True
        
        logger.info("=" * 60)
        if success:
            logger.info("THE UNIFIED CORE - ONLINE")
        else:
            logger.warning("THE UNIFIED CORE - PARTIAL INITIALIZATION")
        logger.info("=" * 60)
        
        return success

    async def _init_database_layer(self) -> bool:
        """Initialize Data & Persistence Layer."""
        logger.info("[1/6] Initializing Database Layer...")
        try:
            self.postgres = PostgresManager(
                host=self.config["postgres_host"],
                port=self.config["postgres_port"],
                database=self.config["postgres_db"],
                user=self.config["postgres_user"],
                password=self.config["postgres_password"]
            )
            self.vector_db = VectorDBManager(
                host=self.config["milvus_host"],
                port=self.config["milvus_port"]
            )
            self.graph_db = GraphDBManager(
                uri=self.config["neo4j_uri"],
                user=self.config["neo4j_user"],
                password=self.config["neo4j_password"]
            )
            self.data_router = DataRouter(
                postgres=self.postgres,
                vector_db=self.vector_db,
                graph_db=self.graph_db
            )
            await self.data_router.initialize_all()
            return True
        except Exception as e:
            logger.error(f"Database init failed: {e}")
            return False

    async def _init_comm_layer(self) -> bool:
        """Initialize Messaging & Communication Layer."""
        logger.info("[2/6] Initializing Communication Layer...")
        try:
            self.message_broker = MessageBroker(
                router_port=self.config["broker_router_port"],
                pub_port=self.config["broker_pub_port"]
            )
            await self.message_broker.start()
            return True
        except Exception as e:
            logger.error(f"MessageBroker init failed: {e}")
            return False

    async def _init_security_layer(self) -> bool:
        """Initialize Security & Governance Layer."""
        logger.info("[3/6] Initializing Security Layer...")
        try:
            self.secops = SecOpsAgent()
            self.dev_agent = DevAgent(secops_agent=self.secops)
            return True
        except Exception as e:
            logger.error(f"Security layer init failed: {e}")
            return False

    async def _init_resource_layer(self) -> bool:
        """Initialize Resource Management & F/S Layer."""
        logger.info("[4/6] Initializing Resource Layer...")
        try:
            self.resource_monitor = ResourceMonitor(
                gpu_enabled=self.config["gpu_enabled"]
            )
            await self.resource_monitor.initialize()
            
            self.process_manager = ProcessManager()
            await self.process_manager.initialize()
            
            self.filesystem = SecureFileSystem(
                allowed_roots=self.config["allowed_roots"]
            )
            return True
        except Exception as e:
            logger.error(f"Resource layer init failed: {e}")
            return False

    async def _init_neural_layer(self) -> bool:
        """Initialize Cognitive & Generative Layer."""
        logger.info("[5/6] Initializing Neural Layer...")
        try:
            self.multimodal_hub = MultimodalHub()
            from unified_core.multimodal import GenerationType
            text_gen = TextGenerator(model_name=self.config["llm_model"])
            self.multimodal_hub.register_generator(GenerationType.TEXT, text_gen)
            return True
        except Exception as e:
            logger.error(f"Neural layer init failed: {e}")
            return False

    async def _start_background_services(self) -> None:
        """Boot secondary background monitoring services."""
        logger.info("[6/6] Starting Background Services...")
        try:
            if self.resource_monitor:
                await self.resource_monitor.start_continuous_monitoring(interval_seconds=10)
        except Exception as e:
            logger.error(f"Background services failed: {e}")

    
    async def shutdown(self):
        """Graceful shutdown of all subsystems."""
        logger.info("Shutting down The Unified Core...")
        self._running = False
        
        # Shutdown in reverse order
        if self.resource_monitor:
            await self.resource_monitor.shutdown()
        
        if self.message_broker:
            await self.message_broker.stop()
        
        if self.data_router:
            await self.data_router.close_all()
        
        self._shutdown_event.set()
        logger.info("The Unified Core - Shutdown complete")
    
    async def run_forever(self):
        """Run until shutdown signal."""
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        await self._shutdown_event.wait()
    
    # ========================================
    # High-Level API
    # ========================================
    
    async def query(self, input_data, **kwargs):
        """Universal query interface."""
        return await self.data_router.query(input_data, **kwargs)
    
    async def store(self, input_data, **kwargs):
        """Universal store interface."""
        return await self.data_router.store(input_data, **kwargs)
    
    async def generate_code(self, task: str, language: str = "python"):
        """Generate code for a task."""
        from unified_core.dev_agent import GenerationRequest, CodeLanguage
        
        request = GenerationRequest(
            task_description=task,
            language=CodeLanguage(language)
        )
        return await self.dev_agent.generate(request)
    
    async def generate_text(self, prompt: str, **kwargs):
        """Generate text using LLM."""
        from unified_core.multimodal import GenerationRequest, GenerationType
        
        request = GenerationRequest(
            prompt=prompt,
            generation_type=GenerationType.TEXT,
            **kwargs
        )
        return await self.multimodal_hub.generate(request)
    
    async def get_system_status(self) -> Dict:
        """Get current system status."""
        snapshot = await self.resource_monitor.get_snapshot()
        
        return {
            "status": "online" if self._running else "offline",
            "cpu_percent": snapshot.cpu.usage_percent,
            "memory_percent": snapshot.memory.usage_percent,
            "gpu_count": len(snapshot.gpus),
            "gpu_memory_percent": max((g.memory_percent for g in snapshot.gpus), default=0),
            "process_count": snapshot.process_count,
            "uptime_hours": snapshot.uptime_seconds / 3600,
            "agents": len(self.message_broker.get_agents()) if self.message_broker else 0
        }


async def main():
    """Main entry point."""
    core = UnifiedCore()
    
    if await core.initialize():
        logger.info("System ready. Press Ctrl+C to shutdown.")
        await core.run_forever()
    else:
        logger.error("Initialization failed. Exiting.")


if __name__ == "__main__":
    asyncio.run(main())
