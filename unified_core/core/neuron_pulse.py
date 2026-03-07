"""
Neuron Pulse System — Keeps ALL neurons alive and active
=========================================================

Problem: 9,482 neurons exist but only ~10 get activated per session.
Solution: Systematic domain rotation + event-driven activation.

Architecture:
  CoreLoop calls pulse(cycle) every cycle →
    1. Rotate through domains (trading, evolution, security, system, etc.)
    2. Activate neurons relevant to current system state
    3. Learn from outcomes (Hebbian reinforcement)
    4. Prevent energy decay by keeping neurons stimulated

CRITICAL: This runs IN the CoreLoop — must be <50ms per call.
"""

import logging
import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger("unified_core.core.neuron_pulse")


class NeuronPulse:
    """
    Systematic neuron activator — keeps the entire fabric alive.
    
    Strategy: rotate through domains each cycle so ALL neurons
    get activated regularly, not just monitoring ones.
    """
    
    # Domain rotation — each domain gets pulsed in turn
    PULSE_DOMAINS = [
        # (domain_name, query_keywords, interval_cycles)
        ("trading", "trading signal LONG SHORT profit loss win rate SL TP", 3),
        ("evolution", "evolution innovation refactoring code improvement bug fix", 5),
        ("security", "security vulnerability audit hardening protection firewall", 7),
        ("monitoring", "CPU RAM memory disk system health monitor", 10),
        ("intelligence", "reasoning decision intelligence analysis prediction", 5),
        ("survival", "backup resilience recovery protection data loss", 10),
        ("general", "agent worker task capability performance", 8),
    ]
    
    # Event-driven queries — triggered by system state
    EVENT_QUERIES = {
        "high_cpu": "CPU stress overload resource management throttle",
        "high_mem": "memory pressure optimization cleanup cache",
        "trade_signal": "trading signal confidence market regime trend",
        "evolution_success": "evolution success promotion improvement validated",
        "evolution_failure": "evolution failure rollback rejection error",
        "agent_task": "agent task dispatch orchestrator health monitor",
        "neural_online": "neural engine brain thinking reasoning online",
        "neural_offline": "neural engine offline fallback degraded",
    }
    
    def __init__(self):
        self._fabric = None
        self._cycle_offset = 0  # Tracks which domain to pulse next
        self._total_activations = 0
        self._total_learnings = 0
        self._last_pulse_time = 0
        self._domain_stats: Dict[str, int] = {}
        logger.info("⚡ NeuronPulse initialized")
    
    def _get_fabric(self):
        """Lazy-load NeuronFabric."""
        if self._fabric is None:
            try:
                from unified_core.core.neuron_fabric import get_neuron_fabric
                self._fabric = get_neuron_fabric()
            except Exception:
                return None
        return self._fabric
    
    def pulse(self, cycle: int, system_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main pulse — called every cycle from CoreLoop.
        
        1. Domain rotation pulse (deterministic)
        2. Event-driven activation (reactive)
        3. Cascade activation (spreading)
        
        Returns: activation stats
        """
        fabric = self._get_fabric()
        if not fabric:
            return {"skipped": True}
        
        start = time.time()
        total_activated = 0
        state = system_state or {}
        
        # 1. Domain rotation — one domain per cycle
        domain_activated = self._pulse_domain(cycle, fabric)
        total_activated += domain_activated
        
        # 2. Event-driven activation — react to system state
        event_activated = self._pulse_events(state, fabric)
        total_activated += event_activated
        
        # 3. Bulk vitality boost — every 25 cycles, touch ALL alive neurons
        if cycle % 25 == 0:
            bulk = self._bulk_vitality_boost(fabric)
            total_activated += bulk
        
        # 4. Save periodically
        if cycle % 100 == 0 and total_activated > 0:
            try:
                fabric._save()
            except Exception:
                pass
        
        elapsed_ms = (time.time() - start) * 1000
        self._total_activations += total_activated
        
        if total_activated > 0 and cycle % 50 == 0:
            logger.info(
                f"⚡ NeuronPulse: {total_activated} activated this cycle, "
                f"{self._total_activations} total | {elapsed_ms:.0f}ms"
            )
        
        return {
            "activated": total_activated,
            "total_activations": self._total_activations,
            "elapsed_ms": elapsed_ms,
        }
    
    def _pulse_domain(self, cycle: int, fabric) -> int:
        """Rotate through domains — activate neurons for one domain per cycle."""
        activated_count = 0
        
        for domain, query, interval in self.PULSE_DOMAINS:
            if cycle % interval != 0:
                continue
            
            try:
                # Activate by query (matches word overlap in propositions+tags)
                activated = fabric.activate_by_query(query, top_k=15)
                activated_count += len(activated)
                
                # Also activate by domain directly — use fabric.activate()
                domain_neurons = fabric.get_neurons_by_domain(domain)
                batch_size = min(20, len(domain_neurons))
                
                for neuron in domain_neurons[:batch_size]:
                    if neuron.is_alive:
                        result = fabric.activate(neuron.neuron_id, signal=0.6, depth=1)
                        activated_count += len(result)
                
                self._domain_stats[domain] = self._domain_stats.get(domain, 0) + activated_count
                
            except Exception:
                pass
        
        return activated_count
    
    def _pulse_events(self, state: Dict[str, Any], fabric) -> int:
        """React to system events with targeted neuron activation."""
        activated_count = 0
        
        # CPU stress
        cpu = state.get("cpu_percent", 0)
        if cpu > 50:
            activated = fabric.activate_by_query(self.EVENT_QUERIES["high_cpu"], top_k=5)
            activated_count += len(activated)
        
        # Memory pressure
        mem = state.get("mem_percent", 0)
        if mem > 70:
            activated = fabric.activate_by_query(self.EVENT_QUERIES["high_mem"], top_k=5)
            activated_count += len(activated)
        
        # Neural Engine status
        neural = state.get("neural_alive", True)
        query = self.EVENT_QUERIES["neural_online" if neural else "neural_offline"]
        activated = fabric.activate_by_query(query, top_k=3)
        activated_count += len(activated)
        
        # Trading activity
        if state.get("trading_active"):
            activated = fabric.activate_by_query(self.EVENT_QUERIES["trade_signal"], top_k=5)
            activated_count += len(activated)
        
        # Agent tasks dispatched
        if state.get("agents_dispatched"):
            activated = fabric.activate_by_query(self.EVENT_QUERIES["agent_task"], top_k=5)
            activated_count += len(activated)
        
        return activated_count
    
    def _bulk_vitality_boost(self, fabric) -> int:
        """
        Every 25 cycles: touch ALL alive neurons with a small energy pulse.
        Prevents mass death from time decay.
        """
        boosted = 0
        try:
            for neuron in list(fabric._neurons.values()):
                if neuron.is_alive and neuron.energy < 0.5:
                    # Small energy boost — not full recharge
                    neuron.energy = min(1.0, neuron.energy + 0.05)
                    boosted += 1
            
            # Track in fabric counter too
            if boosted > 0:
                fabric._total_activations += boosted
                logger.debug(f"⚡ Bulk vitality boost: {boosted} neurons recharged")
        except Exception:
            pass
        
        return boosted
    
    def learn_from_trade(self, symbol: str, direction: str,
                         success: bool, confidence: float = 0.5):
        """Learn from a trading result — reinforce/punish trading neurons."""
        fabric = self._get_fabric()
        if not fabric:
            return
        
        try:
            query = f"trading {symbol} {direction} signal market"
            activated = fabric.activate_by_query(query, top_k=8)
            if activated:
                fabric.learn_from_outcome(activated, success=success, impact=confidence)
                self._total_learnings += 1
        except Exception:
            pass
    
    def learn_from_evolution(self, proposal_type: str, target: str, 
                             success: bool):
        """Learn from evolution outcome — reinforce/punish evolution neurons."""
        fabric = self._get_fabric()
        if not fabric:
            return
        
        try:
            file_short = target.split("/")[-1] if "/" in target else target
            query = f"evolution {proposal_type} {file_short} code improvement"
            activated = fabric.activate_by_query(query, top_k=8)
            if activated:
                fabric.learn_from_outcome(activated, success=success, impact=0.6)
                self._total_learnings += 1
        except Exception:
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pulse statistics."""
        return {
            "total_activations": self._total_activations,
            "total_learnings": self._total_learnings,
            "domain_stats": self._domain_stats,
        }


# Singleton
_pulse_instance: Optional[NeuronPulse] = None


def get_neuron_pulse() -> NeuronPulse:
    """Get or create global NeuronPulse instance."""
    global _pulse_instance
    if _pulse_instance is None:
        _pulse_instance = NeuronPulse()
    return _pulse_instance
