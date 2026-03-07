"""
Neuron Learning Bridge — Connects Evolution Pipeline to NeuronFabric
Version: 1.0.0

Transforms evolution outcomes (promotions, rejections, policy blocks)
into meaningful cognitive neurons and Hebbian learning signals.

Instead of creating monitoring noise ("CPU:0.4%"), this creates
knowledge neurons that encode what the system learned:
  ✅ "early_return pattern improves recall_engine.recall" (cognitive)
  ❌ "isinstance spam rejected for neural_bridge.get_stats" (warning)
  🎯 "neural_engine files need careful error handling" (strategic)
"""

import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger("unified_core.evolution.neuron_learning")


class NeuronLearningBridge:
    """
    Bridge between Evolution outcomes and NeuronFabric learning.
    
    For each evolution outcome:
    1. Creates a COGNITIVE neuron encoding the lesson learned
    2. Activates related neurons (by file/domain)
    3. Calls learn_from_outcome() to strengthen/weaken synapses
    4. Periodically saves the fabric
    """
    
    def __init__(self):
        self._fabric = None
        self._save_counter = 0
        self._save_interval = 10  # Save fabric every 10 learnings
        self._total_lessons = 0
        self._success_lessons = 0
        self._failure_lessons = 0
        logger.info("🧬 NeuronLearningBridge initialized")
    
    def _get_fabric(self):
        """Lazy-load NeuronFabric to avoid circular imports."""
        if self._fabric is None:
            try:
                from unified_core.core.neuron_fabric import get_neuron_fabric
                self._fabric = get_neuron_fabric()
                logger.info(f"🧬 NeuronFabric connected: {len(self._fabric._neurons)} neurons")
            except Exception as e:
                logger.warning(f"NeuronFabric not available: {e}")
        return self._fabric
    
    def learn_from_promotion(self, proposal_id: str, proposal: Any, 
                              apply_result: Dict[str, Any]) -> None:
        """
        A proposal was PROMOTED (applied successfully).
        
        Creates a cognitive neuron: "Pattern X works for function Y in file Z"
        Then reinforces related neurons via Hebbian learning.
        """
        fabric = self._get_fabric()
        if not fabric:
            return
        
        try:
            from unified_core.core.neuron_fabric import NeuronType
            
            # Extract context
            target = proposal.targets[0] if proposal.targets else "unknown"
            file_short = target.split("/")[-1] if "/" in target else target
            description = proposal.description or "code improvement"
            risk = proposal.risk_score
            
            # Create cognitive neuron encoding the lesson
            proposition = f"✅ {description} — risk={risk}, file={file_short}"
            
            neuron = fabric.create_neuron(
                proposition=proposition,
                neuron_type=NeuronType.COGNITIVE,
                confidence=min(0.9, 1.0 - (risk / 100)),
                domain="evolution",
                tags=["evolution", "success", file_short],
                energy=0.8,
                metadata={
                    "proposal_id": proposal_id,
                    "target": target,
                    "risk": risk,
                    "timestamp": time.time(),
                    "type": "promotion"
                }
            )
            
            # Auto-connect to related neurons
            fabric.auto_connect(neuron.neuron_id, max_connections=5)
            
            # Activate related neurons and learn (Hebbian reinforcement)
            query = f"evolution {file_short} success"
            activated = fabric.activate_by_query(query, top_k=5)
            
            if activated:
                fabric.learn_from_outcome(activated, success=True, impact=0.8)
                logger.info(
                    f"🧠 Neuron learned from promotion: {neuron.neuron_id[:8]} "
                    f"({len(activated)} related neurons reinforced)"
                )
            
            self._success_lessons += 1
            self._total_lessons += 1
            self._maybe_save(fabric)
            
        except Exception as e:
            logger.error(f"Failed to learn from promotion: {e}")
    
    def learn_from_rejection(self, proposal_id: str, proposal: Any,
                              phase: str, error: str) -> None:
        """
        A proposal was REJECTED (canary failed, policy blocked, apply failed).
        
        Creates a cognitive neuron: "Pattern X dangerous for function Y"
        Then weakens related neurons via Anti-Hebbian learning.
        """
        fabric = self._get_fabric()
        if not fabric:
            return
        
        try:
            from unified_core.core.neuron_fabric import NeuronType
            
            target = proposal.targets[0] if proposal.targets else "unknown"
            file_short = target.split("/")[-1] if "/" in target else target
            description = proposal.description or "code change"
            
            # Shorten error for proposition
            error_short = error[:80] if error else "unknown error"
            
            proposition = f"❌ [{phase}] {description} — {error_short}"
            
            neuron = fabric.create_neuron(
                proposition=proposition,
                neuron_type=NeuronType.COGNITIVE,
                confidence=0.7,  # High confidence in the failure pattern
                domain="evolution",
                tags=["evolution", "failure", phase, file_short],
                energy=0.6,
                metadata={
                    "proposal_id": proposal_id,
                    "target": target,
                    "phase": phase,
                    "error": error_short,
                    "timestamp": time.time(),
                    "type": "rejection"
                }
            )
            
            fabric.auto_connect(neuron.neuron_id, max_connections=5)
            
            # Activate related neurons and learn (Anti-Hebbian weakening)
            query = f"evolution {file_short} {phase}"
            activated = fabric.activate_by_query(query, top_k=5)
            
            if activated:
                fabric.learn_from_outcome(activated, success=False, impact=0.5)
                logger.info(
                    f"🧠 Neuron learned from {phase}: {neuron.neuron_id[:8]} "
                    f"({len(activated)} related neurons weakened)"
                )
            
            self._failure_lessons += 1
            self._total_lessons += 1
            self._maybe_save(fabric)
            
        except Exception as e:
            logger.error(f"Failed to learn from rejection: {e}")
    
    def learn_from_policy_block(self, proposal_id: str, violations: list,
                                 target: str) -> None:
        """
        A proposal was BLOCKED by the Policy Gate (before canary).
        
        Creates a warning neuron so the system remembers what's banned.
        """
        fabric = self._get_fabric()
        if not fabric:
            return
        
        try:
            from unified_core.core.neuron_fabric import NeuronType
            
            file_short = target.split("/")[-1] if "/" in target else target
            violations_short = "; ".join(v[:50] for v in violations[:3])
            
            proposition = f"🚫 Policy blocked for {file_short}: {violations_short}"
            
            neuron = fabric.create_neuron(
                proposition=proposition,
                neuron_type=NeuronType.META,  # Meta: knowledge about the system itself
                confidence=0.95,  # Very confident — these are rules
                domain="evolution",
                tags=["evolution", "policy", "blocked", file_short],
                energy=0.9,  # High energy — important to remember
                metadata={
                    "proposal_id": proposal_id,
                    "violations": violations,
                    "target": target,
                    "timestamp": time.time(),
                    "type": "policy_block"
                }
            )
            
            fabric.auto_connect(neuron.neuron_id, max_connections=3)
            
            self._total_lessons += 1
            self._maybe_save(fabric)
            
            logger.info(f"🧠 Policy lesson recorded: {neuron.neuron_id[:8]}")
            
        except Exception as e:
            logger.error(f"Failed to learn from policy block: {e}")
    
    def _maybe_save(self, fabric) -> None:
        """Save fabric periodically to avoid data loss."""
        self._save_counter += 1
        if self._save_counter >= self._save_interval:
            try:
                fabric.save()
                logger.info(f"💾 NeuronFabric saved ({self._total_lessons} lessons total)")
                self._save_counter = 0
            except Exception as e:
                logger.error(f"Failed to save NeuronFabric: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Learning statistics."""
        return {
            "total_lessons": self._total_lessons,
            "success_lessons": self._success_lessons,
            "failure_lessons": self._failure_lessons,
            "save_counter": self._save_counter,
        }


# Singleton
_bridge_instance: Optional[NeuronLearningBridge] = None

def get_neuron_learning_bridge() -> NeuronLearningBridge:
    """Get the global NeuronLearningBridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = NeuronLearningBridge()
    return _bridge_instance
