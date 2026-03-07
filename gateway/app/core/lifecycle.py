"""
NOOGH System Life Cycle (The Living Heartbeat)
Integrates all autonomous components into a continuous, self-regulating existence.
"""

import asyncio
import logging
import traceback
from typing import Optional

from neural_engine.autonomic_system.hardware_awareness import get_hardware_consciousness
from neural_engine.autonomic_system.self_governor import get_self_governing_agent
from gateway.app.core.metrics_collector import get_metrics_collector
from gateway.app.ml.auto_curriculum import get_curriculum_learner
from gateway.app.reporting.comprehensive_reporter import get_reporter

logger = logging.getLogger("noogh.lifecycle")


class SystemLifeCycle:
    """
    The 'Soul' of NOOGH.
    Orchestrates the continuous loop of perception, cognition, and action.
    """

    def __init__(self):
        self.running = False
        self.task: Optional[asyncio.Task] = None

        # Connect organs
        self.hw = get_hardware_consciousness()
        self.brain = get_self_governing_agent()
        self.learner = get_curriculum_learner()
        self.senses = get_metrics_collector()
        self.reporter = get_reporter()

        logger.info("🟢 System Life Cycle initialized")

    async def start(self):
        """Start the living heartbeat"""
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._life_loop())
        logger.info("💓 NOOGH is now ALIVE and breathing")

    async def stop(self):
        """Stop the heartbeat"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("🔴 NOOGH hibernating")

    async def _life_loop(self):
        """The continuous existence loop"""
        cycle_count = 0

        while self.running:
            try:
                # 1. Perception (Sense hardware & environment)
                # Runs often (every 10s)
                await self._perception_phase()

                # 2. Cognition (Analyze & Decide)
                # Runs periodically (every 60s)
                if cycle_count % 6 == 0:
                    await self._cognition_phase()

                # 3. Evolution (Learn, Train, Evolve)
                # Runs rarely (every 5 mins)
                if cycle_count % 30 == 0:
                    await self._evolution_phase()

                cycle_count += 1
                await asyncio.sleep(10)  # The heartbeat interval

            except Exception as e:
                logger.error(f"💔 Heartbeat skipped a beat: {e}")
                traceback.print_exc()
                await asyncio.sleep(10)  # Recover

    async def _perception_phase(self):
        """Sense the immediate environment"""
        # Introspect hardware (Update RAM, CPU, GPU stats)
        # This keeps the 'Hardware Consciousness' real-time
        self.hw.full_introspection()

        # Check simple health
        metrics = self.senses.get_performance_snapshot()
        if metrics["error_rate"] > 0.05:
            logger.warning(f"⚠️ High error rate detected: {metrics['error_rate']:.1%}")

    async def _cognition_phase(self):
        """Think about the current state"""
        # Analyze interactions from the last minute
        # This uses Real Data from MetricsCollector
        needs = await self.learner._analyze_interaction_patterns()

        if needs:
            top_need = needs[0]
            logger.info(f"🧠 Thinking: I noticed users need help with {top_need.category} ({top_need.priority:.0%})")

    async def _evolution_phase(self):
        """Grow and Improve"""
        import os
        
        # SECURITY: Disable auto-training by default to save GPU resources
        if os.getenv("NOOGH_AUTO_TRAINING", "0") != "1":
            logger.debug("🛑 Auto-training disabled (set NOOGH_AUTO_TRAINING=1 to enable)")
            return
        
        logger.info("🧬 Evolution Phase: Checking if I should learn something new...")

        # 1. Self-Diagnosis
        analysis = await self.brain.analyze_self()
        if analysis.confidence_score < 0.7:
            logger.info("📉 Confidence low, triggering deeper self-reflection")

        # 2. Auto-Curriculum (Real Training Decision)
        # Only trains if there are REAL high-priority needs
        decisions = await self.learner.decide_training(top_n=1)

        approved = [d for d in decisions if d.approved]
        if approved:
            logger.info(f"🚀 AUTO-EVOLUTION ACTION: Starting training for {len(approved)} skills")
            # Execute auto-training in background to avoid blocking
            asyncio.create_task(self.learner.execute_auto_training())
            logger.info("✅ Auto-training initiated in background")


# Singleton
_lifecycle: Optional[SystemLifeCycle] = None


def get_system_lifecycle() -> SystemLifeCycle:
    global _lifecycle
    if _lifecycle is None:
        _lifecycle = SystemLifeCycle()
    return _lifecycle
