"""
Meta-Cognitive Supervisor (Meta-Governor)
Monitors decision quality, agent performance, and prevents configuration races.
Reflector of Sovereign Intelligence v5.0 Master.
"""

import logging
import time
import asyncio
import uuid
import os
import psutil
from typing import List, Dict, Any, Optional
from datetime import datetime
from unified_core.core.world_model import WorldModel, Observation

logger = logging.getLogger("unified_core.core.meta_governor")

class MetaGovernor:
    def __init__(self, agent_daemon=None):
        self.world_model = WorldModel()
        self.daemon = agent_daemon
        self.id = "meta_governor_aleph"
    
        # Mathematical Governance v5.3
        self._f_t = 0.0  # EWMA Failure Rate
        self._g_t = 0.0  # Failure Gradient (dF/dt)
        self._alpha = 0.2  # Smoothing Factor
    
        self.last_failure_total = 0
        self.ladder_level = 0  # 0=Normal, 1=SoftBrake, 2=Cooldown, 3=PauseSynth, 4=Quarantine
        self._oversight_cycles = 0  
        self.global_state_lock = asyncio.Lock()
        
        # Validation Layers & Resource Health
        self._drift_threshold = 0.3
        self._resource_limits = {
            "max_memory_percent": 85.0,
            "max_cpu_percent": 70.0
        }
        self._cpu_spike_strikes = 0
    
        logger.info("Meta-Cognitive Supervisor initialized | Governance: v5.3 (Symmetric Oversight)")

    async def audit_decision_quality(self, decision_id: str, fragility: float, urgency: float, semantic_context: str = ""):
        """
        Analyzes if a decision was too fragile for its urgency (Async).
        ENHANCED: Added Semantic Drift Detection.
        """
        is_risky = False
        if fragility > 0.6 and urgency > 0.8:
            logger.warning(f"[{self.id}] CRITICAL DISSONANCE: Decision {decision_id} is highly fragile ({fragility}) but extremely urgent ({urgency}).")
            is_risky = True
        
        if semantic_context and "evolution" in semantic_context.lower() and fragility > 0.5:
            logger.info(f"[{self.id}] 🧬 Semantic Drift Check: High-impact evolution decision detected with moderate fragility.")
            is_risky = True

        if is_risky:
            await self.world_model.add_belief(
                proposition=f"METAGOVERNOR_WARNING: Critical cognitive dissonance detected in decision {decision_id}.",
                initial_confidence=0.9
            )

    async def validate_system_coherence(self) -> bool:
        """
        Validation Layer: Identifies conflicting agent goals or decision patterns.
        """
        try:
            state = await self.world_model.get_belief_state()
            active = state.get('active', 0)
            falsified = state.get('falsified', 0)
            
            if active > 10 and falsified > (active * 0.5):
                logger.warning(f"[{self.id}] 🚨 SYSTEM INCOHERENCE: High falsification ratio detected ({falsified}/{active}).")
                return False
            
            return True
        except Exception as e:
            logger.error(f"[{self.id}] Coherence check failed: {e}")
            return True

    async def resource_health_check(self):
        """
        Validation Layer: Oversees agent resource footprints to prevent system starvation.
        Refinement: Non-blocking CPU check and strike system.
        """
        try:
            mem = psutil.virtual_memory().percent
            # psutil.cpu_percent(interval=None) returns percent since last call
            cpu = psutil.cpu_percent(interval=None)
            
            if mem > self._resource_limits["max_memory_percent"]:
                logger.warning(f"[{self.id}] 📉 Resource Stress: RAM at {mem}%. Triggering cognitive dampening.")
                await self._climb_ladder()
            
            if cpu > self._resource_limits["max_cpu_percent"]:
                self._cpu_spike_strikes += 1
                logger.info(f"[{self.id}] Resource Load: CPU Spike at {cpu}% (Strike {self._cpu_spike_strikes}/3)")
            else:
                self._cpu_spike_strikes = 0

            if self._cpu_spike_strikes >= 3:
                logger.warning(f"[{self.id}] Sustained CPU stress. Engaging soft brake.")
                await self._climb_ladder()
                self._cpu_spike_strikes = 0
                
        except Exception as e:
            logger.error(f"[{self.id}] Resource check failed: {e}")

    async def synchronize_agents(self):
        """Prevents Configuration Races (Sub-Specialist arbitration)."""
        return not self.global_state_lock.locked()

    async def evaluate_performance(self):
        """
        Refined Mathematical Governance v5.3.
        Uses failure magnitude (delta) and hysteresis thresholds.
        """
        try:
            state = await self.world_model.get_belief_state()
            current_total = state.get('total_falsifications', 0)
            
            # 1. Improved Failure Signals
            delta = max(0, current_total - self.last_failure_total)
            # Normalize signal: 10 falsifications in a cycle = 1.0 signal
            fail_signal = min(1.0, delta / 10.0)
            
            new_f_t = (self._alpha * fail_signal) + ((1 - self._alpha) * self._f_t)
            self._g_t = new_f_t - self._f_t
            self._f_t = new_f_t
            self.last_failure_total = current_total
            
            if self._f_t > 0.01:
                logger.info(
                    f"[{self.id}] Governance Metrics: F_t={self._f_t:.3f}, G_t={self._g_t:.3f}, delta={delta}"
                )

            # 2. Thresholds with Hysteresis
            threat = (self._f_t > 0.4) or (self._g_t > 0.15)
            recovery = (self._f_t < 0.08) and (self._g_t < 0.02)

            if threat:
                await self._climb_ladder()
            elif recovery and self.ladder_level > 0:
                await self._descend_ladder()

        except Exception as e:
            logger.error(f"[{self.id}] Governance Evaluation failed: {e}")

    async def _climb_ladder(self):
        """Escalate damping actions (Symmetric)."""
        if not self.daemon: return
        
        self.ladder_level = min(4, self.ladder_level + 1)
        reason = f"Predictive instability (F_t={self._f_t:.2f}, G_t={self._g_t:.2f})"
        
        if self.ladder_level == 1:
            logger.warning(f"[{self.id}] STEP 1: Soft Brake (-15% aggression). Reason: {reason}")
            if hasattr(self.daemon, 'adjust_aggression'):
                await self.daemon.adjust_aggression(-0.15)
        elif self.ladder_level == 2:
            logger.warning(f"[{self.id}] STEP 2: Cognitive Cooldown (+5s interval). Reason: {reason}")
            if hasattr(self.daemon, 'adjust_interval'):
                await self.daemon.adjust_interval(5.0)
        elif self.ladder_level == 3:
            logger.warning(f"[{self.id}] STEP 3: Synthesis Pause (cooldown=300s). Reason: {reason}")
            if hasattr(self.world_model, '_synthesis_cooldown'):
                if not hasattr(self.world_model, '_default_synthesis_cooldown'):
                    self.world_model._default_synthesis_cooldown = getattr(self.world_model, '_synthesis_cooldown', 60)
                self.world_model._synthesis_cooldown = 300 
        elif self.ladder_level == 4:
            logger.critical(f"[{self.id}] STEP 4: QUARANTINE. Resetting system parameters. Reason: {reason}")
            if hasattr(self.daemon, 'recalibrate'):
                await self.daemon.recalibrate(f"Critical systemic drift: {reason}")
            self.ladder_level = 0 # Reset ladder after hard recalibrate

    async def _descend_ladder(self):
        """Relax damping as stability returns (Symmetric)."""
        if not self.daemon: return
        
        logger.info(f"[{self.id}] System stabilizing (F_t={self._f_t:.2f}). Relaxing damping...")
        prev = self.ladder_level
        self.ladder_level = max(0, self.ladder_level - 1)
        
        # Step-by-step restoration
        if prev == 3 and hasattr(self.world_model, '_default_synthesis_cooldown'):
            self.world_model._synthesis_cooldown = self.world_model._default_synthesis_cooldown
            logger.info(f"[{self.id}] Restored default synthesis cooldown.")

        if prev == 2 and hasattr(self.daemon, 'adjust_interval'):
            await self.daemon.adjust_interval(-5.0)
            logger.info(f"[{self.id}] Restored nominal cognitive interval.")

        if self.ladder_level == 0 and hasattr(self.daemon, 'adjust_aggression'):
            await self.daemon.adjust_aggression(0.15)
            logger.info(f"[{self.id}] Restored full aggression profiles.")

    async def reflective_deliberation(self):
        """
        PHASE 17: Strategic Eye Protocol
        """
        logger.info(f"[{self.id}] 👁️ Initiating PHASE 17: Reflective Deliberation session...")
        try:
            if self.daemon and hasattr(self.daemon, "_planning_engine"):
                briefs = []
                if hasattr(self.daemon, 'get_semantic_brief'):
                    brief = await self.daemon.get_semantic_brief()
                    briefs.append(brief)
                
                if briefs:
                    decision = await self.daemon._planning_engine.consult_brain(briefs)
                    logger.warning(f"[{self.id}] 📜 STRATEGIC EVOLUTION RECORDED: Path='{decision.get('path')}' | Eye='{decision.get('eye')}'")
            
            await self.evolution_audit()
        except Exception as e:
            logger.error(f"[{self.id}] Reflective Deliberation error: {e}")

    async def evolution_audit(self):
        """
        Cognitive Depth: Monitors success rate of self-healing.
        """
        try:
            history = await self.world_model.get_evolution_history(limit=20)
            if not history: return
            
            successes = sum(1 for step in history if step.get('success'))
            rate = successes / len(history)
            
            logger.info(f"[{self.id}] 🧬 Evolution Audit: {rate*100:.1f}% success rate over last {len(history)} steps.")
            
            if rate < 0.6:
                logger.warning(f"[{self.id}] 🚨 LOW EVOLUTION SUCCESS: Cognitive decay detected in self-healing.")
                await self._climb_ladder()
        except Exception as e:
            logger.error(f"[{self.id}] Evolution audit failed: {e}")

    async def run_forever(self):
        """Autonomous Oversight Cycle (Infinite)."""
        await self.world_model.setup()
        
        while True:
            self._oversight_cycles += 1
            
            # Parallel Oversight Checks
            await asyncio.gather(
                self.evaluate_performance(),
                self.resource_health_check(),
                self.validate_system_coherence()
            )
            
            # Periodic Tasks
            state = await self.world_model.get_belief_state()
            if state.get('total_beliefs', 0) > 45000:
                logger.info(f"[{self.id}] Memory Bloom detected (Approaching HARD_CAP).")
            
            if self._oversight_cycles % 10 == 0:
                await self.reflective_deliberation()
            
            if self._oversight_cycles % 20 == 0:
                await self._check_evolution_layer()
            
            await asyncio.sleep(30)
    
    async def _check_evolution_layer(self):
        """PHASE 17.5: Evolution Control."""
        try:
            from unified_core.evolution import get_evolution_ledger
            ledger = get_evolution_ledger()
            if ledger.is_safe_mode():
                logger.critical(f"[{self.id}] 🚨 EVOLUTION SAFE MODE ACTIVE")
                return
            stats = ledger.get_stats()
            logger.info(f"[{self.id}] 🧬 Evolution Stats: Success Rate = {stats['success_rate']*100:.1f}%")
        except:
            pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gov = MetaGovernor()
    asyncio.run(gov.run_forever())
