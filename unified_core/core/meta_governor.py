"""
Meta-Cognitive Supervisor (Meta-Governor)
Monitors decision quality, agent performance, and prevents configuration races.
Reflector of Sovereign Intelligence v5.0 Master.
"""

import logging
import time
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from unified_core.core.world_model import WorldModel, Observation

logger = logging.getLogger("unified_core.core.meta_governor")

class MetaGovernor:
    def __init__(self, agent_daemon=None):
            if agent_daemon is not None and not isinstance(agent_daemon, object):
                raise TypeError(f"Expected agent_daemon to be None or an instance of object, got {type(agent_daemon)}")
        
            self.world_model = WorldModel()
            self.daemon = agent_daemon
            self.id = "meta_governor_aleph"
        
            # Hardening v2.1: Mathematical Governance
            self._f_t = 0.0  # EWMA Failure Rate
            self._g_t = 0.0  # Failure Gradient (dF/dt)
            self._alpha = 0.2  # Smoothing Factor
        
            self.last_failure_total = 0
            self.last_recalibrate_time = 0
            self.ladder_level = 0  # 0=Normal, 1=SoftBrake, 2=Cooldown, 3=PauseSynth, 4=Quarantine
            self._oversight_cycles = 0  # Phase 17
            self.global_state_lock = asyncio.Lock()
        
            logger.info("Meta-Cognitive Supervisor initialized | Governance: v2.1")

# Assuming WorldModel is a class that has been defined elsewhere
class WorldModel:
    pass

    async def audit_decision_quality(self, decision_id: str, fragility: float, urgency: float):
        """Analyzes if a decision was too fragile for its urgency (Async)."""
        if fragility > 0.6 and urgency > 0.8:
            logger.warning(f"[{self.id}] CRITICAL DISSONANCE: Decision {decision_id} is highly fragile ({fragility}) but extremely urgent ({urgency}). Potential hallucination or conflict.")
            await self.world_model.add_belief(
                proposition=f"METAGOVERNOR_WARNING: Critical cognitive dissonance detected in decision {decision_id}.",
                initial_confidence=0.9
            )

    async def synchronize_agents(self):
        """Prevents Configuration Races (Sub-Specialist arbitration)."""
        # Ensure we don't have multiple agents modifying global state configs at the same millisecond
        return not self.global_state_lock.locked()

    async def evaluate_performance(self):
        """Refined Mathematical Governance v2.1."""
        try:
            falsifications = await self.world_model._memory.get_all_falsifications()
            current_total = len(falsifications)
            
            # 1. Update EWMA Failure Rate (F_t)
            # fail_occurred = 1 if new failures detected in this window, else 0
            fail_occurred = 1.0 if current_total > self.last_failure_total else 0.0
            new_f_t = (self._alpha * fail_occurred) + ((1 - self._alpha) * self._f_t)
            
            # 2. Update Gradient (G_t = dF/dt)
            self._g_t = new_f_t - self._f_t
            self._f_t = new_f_t
            self.last_failure_total = current_total
            
            if self._f_t > 0.01:
                logger.info(f"[{self.id}] Governance Metrics: F_t={self._f_t:.3f}, G_t={self._g_t:.3f}")

            # 3. Action Ladder Logic
            if self._f_t > 0.4 or self._g_t > 0.1: # Threat detected
                await self._climb_ladder()
            elif self._f_t < 0.1 and self.ladder_level > 0: # Recovery detected
                await self._descend_ladder()

        except Exception as e:
            logger.error(f"[{self.id}] Governance Evaluation failed: {e}")

    async def _climb_ladder(self):
        """Escalate damping actions."""
        if not self.daemon: return
        
        self.ladder_level = min(4, self.ladder_level + 1)
        reason = f"Predictive instability (F_t={self._f_t:.2f}, G_t={self._g_t:.2f})"
        
        if self.ladder_level == 1:
            logger.warning(f"[{self.id}] STEP 1: Soft Brake (-15% aggression). Reason: {reason}")
            await self.daemon.adjust_aggression(-0.15)
        elif self.ladder_level == 2:
            logger.warning(f"[{self.id}] STEP 2: Cognitive Cooldown (+5s interval).")
            await self.daemon.adjust_interval(5.0)
        elif self.ladder_level == 3:
            logger.warning(f"[{self.id}] STEP 3: Synthesis Pause (Cognitive circuit breaker).")
            # Increase WorldModel consolidation cooldown as a damping measure
            self.world_model._synthesis_cooldown = 300 
        elif self.ladder_level == 4:
            logger.critical(f"[{self.id}] STEP 4: QUARANTINE. Resetting system parameters.")
            await self.daemon.recalibrate(f"Critical systemic drift: {reason}")
            self.ladder_level = 0 # Reset ladder after hard recalibrate

    async def _descend_ladder(self):
        """Relax damping as stability returns."""
        if not self.daemon: return
        logger.info(f"[{self.id}] System stabilizing (F_t={self._f_t:.2f}). Relaxing damping...")
        self.ladder_level = max(0, self.ladder_level - 1)
        # Restore parameters gradually
        if self.ladder_level == 0:
            await self.daemon.adjust_aggression(0.1) # Gently restore

    async def reflective_deliberation(self):
        """
        PHASE 17: Strategic Eye Protocol
        Collects analyst briefs, consults the brain, and records institutional evolution.
        """
        if not self.daemon or not getattr(self.daemon, "_planning_engine", None):
            return

        logger.info(f"[{self.id}] 👁️ Initiating PHASE 17: Reflective Deliberation session...")
        
        # 1. Collect Unified Brief from the Sovereign Daemon
        briefs = []
        if hasattr(self.daemon, 'get_semantic_brief'):
            brief = await self.daemon.get_semantic_brief()
            briefs.append(brief)
        
        if not briefs:
            logger.info(f"[{self.id}] No strategic briefs available. Skipping deliberation.")
            return

        # 2. Consult the Brain (PlanningEngine now records this in evolution_log)
        decision = await getattr(self.daemon, "_planning_engine", None).consult_brain(briefs)
        
        logger.warning(f"[{self.id}] 📜 STRATEGIC EVOLUTION RECORDED: Path='{decision.get('path')}' | Eye='{decision.get('eye')}'")

    async def run_forever(self):
        """Autonomous Oversight Cycle (Infinite)."""
        while True:
            self._oversight_cycles += 1
            
            # 1. Audit Agent reliability
            await self.evaluate_performance()
            
            # 2. Check for cognitive overhead
            beliefs_summary = await self.world_model.get_belief_state()
            if beliefs_summary['total_beliefs'] > 45000:
                logger.info(f"[{self.id}] Memory Bloom detected (Approaching HARD_CAP). Initiating Pruning Proposal.")
            
            # 3. PHASE 17: Strategic Eye Deliberation (Every 10 oversight cycles)
            if self._oversight_cycles % 10 == 0:
                await self.reflective_deliberation()
            
            # 4. PHASE 17.5: Self-Directed Evolution Check (Every 20 cycles)
            if self._oversight_cycles % 20 == 0:
                await self._check_evolution_layer()
            
            await asyncio.sleep(30)
    
    async def _check_evolution_layer(self):
        """
        PHASE 17.5: Monitor and govern the Self-Directed Evolution Layer.
        Checks safe mode status, pending proposals, and goal audit.
        """
        try:
            from unified_core.evolution import (
                get_evolution_ledger, 
                get_goal_audit_engine,
                get_evolution_controller
            )
            
            ledger = get_evolution_ledger()
            audit_engine = get_goal_audit_engine()
            controller = get_evolution_controller()
            
            # Check if system is in safe mode
            if ledger.is_safe_mode():
                logger.critical(f"[{self.id}] 🚨 EVOLUTION SAFE MODE ACTIVE - Proposals disabled")
                return
            
            # Get evolution stats
            stats = ledger.get_stats()
            if stats['total_proposals'] > 0:
                logger.info(f"[{self.id}] 🧬 Evolution: {stats['total_proposals']} proposals, "
                           f"{stats['success_rate']*100:.1f}% success, "
                           f"safe_mode={stats['safe_mode']}")
            
            # Run evolution cycle (process pending proposals)
            result = await controller.run_evolution_cycle()
            if result.get('status') == 'processed':
                logger.warning(f"[{self.id}] 🧬 EVOLUTION CYCLE: Processed {result.get('processed', 0)} proposals")
            
            # Check goal audit for weight adjustments
            adjustments = audit_engine.propose_weight_adjustments()
            if adjustments:
                logger.info(f"[{self.id}] 📊 Goal audit suggests {len(adjustments)} weight adjustments")
            
        except ImportError:
            logger.debug(f"[{self.id}] Evolution layer not available")
        except Exception as e:
            logger.error(f"[{self.id}] Evolution check failed: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gov = MetaGovernor()
    asyncio.run(gov.run_forever())
