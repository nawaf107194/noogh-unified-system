"""
NOOGH Autonomic Task Worker

Background worker that processes autonomic tasks:
- Initiative Loop (self-directed task generation)
- Dream Processing (offline insight generation)
- Self-Governance (health monitoring & self-improvement)

This module is the entry point for the noogh-autonomic.service
"""

import asyncio
import logging
import signal
import sys
import os

# Ensure src is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger("neural_engine.autonomic.task_worker")

# Graceful shutdown flag
_shutdown = False


def _signal_handler(signum, frame):
    global _shutdown
    logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
    _shutdown = True


class AutonomicTaskWorker:
    """
    Background worker that runs autonomic subsystems.
    
    Subsystems:
    - InitiativeLoop: generates self-directed tasks
    - DreamProcessor: offline creative processing
    - SelfGovernor: system health and self-improvement
    """

    def __init__(self):
        self.running = False
        self.cycle_count = 0
        self._initiative = None
        self._governor = None
        self._dream = None

    async def initialize(self):
        """Initialize autonomic subsystems."""
        logger.info("🔧 Initializing Autonomic Task Worker...")

        # Import subsystems with graceful fallback
        try:
            from neural_engine.autonomic_system.initiative_loop import InitiativeLoop
            self._initiative = InitiativeLoop()
            logger.info("  ✅ InitiativeLoop loaded")
        except Exception as e:
            logger.warning(f"  ⚠️ InitiativeLoop unavailable: {e}")

        try:
            from neural_engine.autonomic_system.self_governor import get_self_governing_agent
            self._governor = get_self_governing_agent()
            logger.info("  ✅ SelfGovernor loaded")
        except Exception as e:
            logger.warning(f"  ⚠️ SelfGovernor unavailable: {e}")

        try:
            from neural_engine.autonomic_system.dream_processor import DreamProcessor
            # DreamProcessor needs memory_manager, recall_engine, reasoning_engine
            memory_mgr = recall_eng = reasoning_eng = None
            try:
                from neural_engine.memory_consolidator import MemoryConsolidator
                memory_mgr = MemoryConsolidator()
            except Exception:
                pass
            try:
                from neural_engine.recall_engine import RecallEngine
                recall_eng = RecallEngine()
            except Exception:
                pass
            try:
                from neural_engine.reasoning_engine import ReasoningEngine
                reasoning_eng = ReasoningEngine()
            except Exception:
                pass
            
            if memory_mgr and recall_eng and reasoning_eng:
                self._dream = DreamProcessor(memory_mgr, recall_eng, reasoning_eng)
                logger.info("  ✅ DreamProcessor loaded (full)")
            else:
                logger.info("  ⚠️ DreamProcessor skipped: missing dependencies")
        except Exception as e:
            logger.warning(f"  ⚠️ DreamProcessor unavailable: {e}")

        logger.info("✅ Autonomic Task Worker initialized")

    async def run(self):
        """Main worker loop."""
        self.running = True
        logger.info("🚀 Autonomic Task Worker starting main loop...")

        while self.running and not _shutdown:
            self.cycle_count += 1

            try:
                # Initiative Loop — every 10 cycles (~30s)
                if self._initiative and self.cycle_count % 10 == 0:
                    try:
                        await asyncio.wait_for(
                            self._run_initiative(),
                            timeout=30.0
                        )
                    except asyncio.TimeoutError:
                        logger.warning("⏰ Initiative loop timed out")
                    except Exception as e:
                        logger.error(f"❌ Initiative loop error: {e}")

                # Self-Governance — every 30 cycles (~90s)
                if self._governor and self.cycle_count % 30 == 0:
                    try:
                        await asyncio.wait_for(
                            self._run_governance(),
                            timeout=30.0
                        )
                    except asyncio.TimeoutError:
                        logger.warning("⏰ Governance cycle timed out")
                    except Exception as e:
                        logger.error(f"❌ Governance error: {e}")

                # Dream Processing — every 100 cycles (~5min)
                if self._dream and self.cycle_count % 100 == 0:
                    try:
                        await asyncio.wait_for(
                            self._run_dream(),
                            timeout=60.0
                        )
                    except asyncio.TimeoutError:
                        logger.warning("⏰ Dream processing timed out")
                    except Exception as e:
                        logger.error(f"❌ Dream processing error: {e}")

            except Exception as e:
                logger.error(f"❌ Worker cycle {self.cycle_count} error: {e}")

            # Sleep between cycles
            await asyncio.sleep(3.0)

        logger.info(f"🛑 Task Worker stopped after {self.cycle_count} cycles")

    async def _run_initiative(self):
        """Run initiative loop cycle."""
        if hasattr(self._initiative, 'run_cycle'):
            await self._initiative.run_cycle()
        elif hasattr(self._initiative, 'generate_tasks'):
            await self._initiative.generate_tasks()

    async def _run_governance(self):
        """Run self-governance cycle."""
        if hasattr(self._governor, 'run_cycle'):
            await self._governor.run_cycle()
        elif hasattr(self._governor, 'evaluate_system'):
            await self._governor.evaluate_system()

    async def _run_dream(self):
        """Run dream processing cycle."""
        if hasattr(self._dream, 'process'):
            await self._dream.process()
        elif hasattr(self._dream, 'dream_cycle'):
            await self._dream.dream_cycle()

    async def shutdown(self):
        """Graceful shutdown."""
        self.running = False
        logger.info("🔌 Autonomic Task Worker shutting down...")


async def main():
    """Entry point for the autonomic task worker."""
    worker = AutonomicTaskWorker()
    
    try:
        await worker.initialize()
        await worker.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"💀 Fatal error: {e}")
        sys.exit(1)
    finally:
        await worker.shutdown()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    # Register signal handlers
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    # Run
    asyncio.run(main())
