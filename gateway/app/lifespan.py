import os
import asyncio
import logging
from config.ports import PORTS
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import os

from fastapi import FastAPI

from gateway.app.core.resource_governor import gpu_manager
from gateway.app.core.health import health_probe
from unified_core.initialization import InitializationBarrier
from unified_core.config.integrity import initialize_directories, verify_integrity

logger = logging.getLogger(__name__)


async def init_chromadb(data_dir: str):
    """Initialize ChromaDB (Neural Memory)"""
    logger.info("Phase 1: Initializing Neural Memory (ChromaDB)...")
    try:
        from neural_engine.memory_consolidator import MemoryConsolidator

        consolidator = MemoryConsolidator(base_dir=data_dir)
        logger.info("ChromaDB initialized successfully.")
        return consolidator
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        return None


async def init_embedding_models():
    """Load Lightweight Models (Embeddings)"""
    logger.info("Phase 2: Loading Embedding Models...")
    try:
        pass
    except Exception as e:
        logger.error(f"Failed to load embeddings: {e}")


async def init_heavy_models_with_checks(secrets: dict):
    """
    Prepare model infrastructure without loading models at startup.
    Models are loaded lazily on first use.
    """
    logger.info("Phase 3: Preparing Model Infrastructure (lazy loading)...")

    stats = gpu_manager.get_stats()
    logger.info(
        f"GPU Status: {stats['free_vram_gb']:.2f}GB / "
        f"{stats['total_vram_gb']:.2f}GB free"
    )

    if secrets.get("NOOGH_LIGHT_MODE") == "1":
        logger.info("✅ Light Mode enabled: Models load on first request")
        return

    try:
        import httpx

        neural_url = os.getenv("NEURAL_ENGINE_URL", "http://127.0.0.1:8002")
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{neural_url}/health")
                if response.status_code == 200:
                    logger.info("✅ Neural Engine proxy reachable")
                else:
                    logger.warning(
                        f"⚠️ Neural Engine returned {response.status_code}"
                    )
        except Exception as e:
            logger.warning(f"⚠️ Neural Engine not reachable: {e}")

        logger.info("✅ Model infrastructure ready")
    except Exception as e:
        logger.error(f"Error preparing model infrastructure: {e}")


async def start_dream_worker(app: FastAPI):
    """Start DreamWorker in background (Handled by AgentDaemon)"""
    # Disabled in Gateway to avoid resource contention
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan with MANDATORY initialization barrier.
    Phase 3 integrated (MemoryWorker).
    """
    logger.info("🚀 Starting NOOGH system with initialization barrier...")

    try:
        # === PHASE 1: CONFIG ===
        InitializationBarrier.register_component("config")
        try:
            initialize_directories()
            verify_integrity()
            InitializationBarrier.mark_ready("config")
        except Exception as e:
            InitializationBarrier.mark_failed("config", str(e))

        # === PHASE 2: CONFIG INTEGRITY ===
        InitializationBarrier.register_component("config_integrity")
        InitializationBarrier.mark_ready("config_integrity")

        # === PHASE 3: AUTH ===
        InitializationBarrier.register_component("auth")
        try:
            # Auth is now handled via FastAPI dependencies (require_bearer, require_admin)
            # No need to pre-register tokens - they're validated on each request
            from unified_core.auth import AuthContext
            
            # Just verify secrets are loaded
            secrets = getattr(app.state, "secrets", {})
            if not secrets.get("NOOGH_ADMIN_TOKEN"):
                raise ValueError("NOOGH_ADMIN_TOKEN not configured")
            
            InitializationBarrier.mark_ready("auth")
        except Exception as e:
            InitializationBarrier.mark_failed("auth", str(e))

        # === PHASE 4: ACTUATORS ===
        InitializationBarrier.register_component("actuators")
        try:
            from unified_core.core.actuators import (
                FilesystemActuator,
                NetworkActuator,
                ProcessActuator,
            )
            InitializationBarrier.mark_ready("actuators")
        except Exception as e:
            InitializationBarrier.mark_failed("actuators", str(e))

        logger.info("Waiting for all components...")
        InitializationBarrier.wait_for_startup(timeout=30.0)
        logger.info("✅ Initialization barrier cleared")

    except Exception as e:
        logger.critical(f"❌ FATAL startup error: {e}")
        raise

    # === NORMAL STARTUP ===
    secrets = getattr(app.state, "secrets", {})
    data_dir = secrets.get("NOOGH_DATA_DIR", ".")

    await init_chromadb(data_dir)
    await init_embedding_models()
    await init_heavy_models_with_checks(secrets)

    # === PHASE 3: MEMORY WORKER ===
    from gateway.app.core.memory_worker import initialize_memory_worker
    from gateway.app.core.memory import SemanticMemory

    logger.info("Phase 3: Initializing MemoryWorker...")
    semantic_memory = SemanticMemory(neural_client=None)
    memory_worker = initialize_memory_worker(semantic_memory)

    await memory_worker.start()
    app.state.memory_worker = memory_worker
    logger.info("✅ MemoryWorker started")

    # === SCHEDULER ===
    from gateway.app.ml.scheduler import TrainingScheduler
    app.state.scheduler = TrainingScheduler()

    await start_dream_worker(app)

    # === SYSTEM LIFECYCLE ===
    from gateway.app.core.lifecycle import get_system_lifecycle
    lifecycle = get_system_lifecycle()
    await lifecycle.start()

    # === CONTINUOUS IMPROVEMENT LOOP ===
    # Disabled in Gateway - Handled by AgentDaemon to avoid resource contention
    pass

    # === ORCHESTRATOR ===
    await init_orchestrator(app)
    
    # === ANALYTICS WS INGESTOR ===
    try:
        import os
        from gateway.app.analytics.ws_ingestor import get_ingestor
        ingestor = get_ingestor()
        ingestor.configure(os.getenv("NEURAL_SERVICE_URL", "http://127.0.0.1:8002"))
        await ingestor.start()
        logger.info("✅ Analytics Ingestor started")
    except Exception as e:
        logger.error(f"❌ Failed to start Analytics Ingestor: {e}")

    yield

    # === SHUTDOWN ===
    logger.info("🛑 Shutting down NOOGH Neural OS")

    if hasattr(app.state, "memory_worker"):
        logger.info("Stopping MemoryWorker (drain)...")
        await app.state.memory_worker.stop(drain=True, timeout=10.0)
        logger.info("✅ MemoryWorker stopped")

    if hasattr(app.state, "orchestrator"):
        await app.state.orchestrator.shutdown()


async def init_orchestrator(app: FastAPI):
    """Initialize Neural Orchestrator"""
    logger.info("Phase 5: Initializing Orchestrator...")
    try:
        from gateway.app.core.local_brain_bridge import LocalBrainBridge
        from neural_engine.orchestrator import (
            NeuralOrchestrator,
            PipelineStage,
        )

        orchestrator = NeuralOrchestrator()
        app.state.orchestrator = orchestrator

        bridge = LocalBrainBridge()
        await orchestrator.register_module(
            "local_brain_bridge", bridge, PipelineStage.REASONING
        )

        from gateway.app.core.tool_execution_bridge import ToolExecutionBridge
        exec_bridge = ToolExecutionBridge()
        await orchestrator.register_module(
            "tool_execution_bridge", exec_bridge, PipelineStage.EXECUTION
        )

        await orchestrator.initialize()
        logger.info("✅ Orchestrator online")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
