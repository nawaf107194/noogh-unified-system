"""
Simple Attention Reinforcement Learning Module
================================================

Lightweight RL that reads attention telemetry from trades and updates:
- Neuron confidence (reinforce/weaken based on PnL)
- Synapse weights (Hebbian learning for co-activation)

Design principles:
- Single file, minimal dependencies
- Easy to enable/disable (just don't call it)
- Reads from existing telemetry (no schema changes)
- Safe updates with clipping and rate limiting
- Clear logging for monitoring

Usage:
    rl = SimpleAttentionRL(fabric, config)
    rl.process_trade_result(trade_result)
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger("unified_core.core.simple_attention_rl")


# ============================================================
#  Configuration
# ============================================================

DEFAULT_CONFIG = {
    # Reinforcement rates (OPTIMIZED FOR LOW FREQUENCY: 3 trades/day)
    "confidence_update_rate": 0.05,  # ±5% per trade (was 0.02) ✅
    "synapse_update_rate": 0.03,     # ±3% per trade (was 0.01) ✅

    # PnL normalization
    "pnl_scale": 50.0,   # Normalize by this amount (was 100) ✅
    "pnl_clip": 2.0,     # Clip normalized PnL to [-2, 2] (was 3) ✅

    # Confidence bounds
    "confidence_min": 0.1,
    "confidence_max": 0.9,  # Cap at 0.9 (was 1.0) for stability ✅

    # Synapse bounds
    "synapse_min": 0.0,
    "synapse_max": 1.0,

    # Filtering (LOWER THRESHOLDS FOR LOW FREQUENCY)
    "min_pnl_for_update": 3.0,   # Ignore trades <$3 profit/loss (was 5) ✅
    "relevance_threshold": 0.08,  # Only update neurons with relevance >0.08 (was 0.1) ✅

    # Safety
    "max_updates_per_trade": 50,  # Limit how many neurons to update
    "enable_hebbian": True,       # Enable synapse updates

    # Skip learning support (NEW)
    "skip_learning_enabled": True,  # Process skip evaluations ✅
    "skip_update_scale": 0.6,       # 60% of normal update rate for skips ✅
}


# ============================================================
#  Data Classes
# ============================================================

@dataclass
class RLStats:
    """Statistics for RL updates"""
    total_trades_processed: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    total_neuron_updates: int = 0
    total_confidence_increased: int = 0
    total_confidence_decreased: int = 0

    total_synapse_updates: int = 0
    total_synapses_created: int = 0

    avg_confidence_delta: List[float] = field(default_factory=list)
    avg_synapse_delta: List[float] = field(default_factory=list)

    last_update_time: float = 0.0


# ============================================================
#  Simple Attention RL
# ============================================================

class SimpleAttentionRL:
    """
    Lightweight reinforcement learning for attention mechanism

    Updates neuron confidence and synapse weights based on trade results.
    Implements credit assignment: neurons activated in profitable trades
    get reinforced, neurons in losing trades get weakened.
    """

    def __init__(self, fabric, config: Dict = None):
        """
        Initialize RL module

        Args:
            fabric: NeuronFabric instance
            config: Configuration dict (uses DEFAULT_CONFIG if None)
        """
        self.fabric = fabric
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.stats = RLStats()

        logger.info(
            f"🎯 SimpleAttentionRL initialized: "
            f"confidence_rate={self.config['confidence_update_rate']:.3f}, "
            f"synapse_rate={self.config['synapse_update_rate']:.3f}"
        )

    def process_trade_result(self, trade_result: Dict) -> Dict[str, Any]:
        """
        Process trade result and update neurons

        Args:
            trade_result: Dict containing:
                - pnl: Profit/loss in dollars
                - result: 'WIN' or 'LOSS'
                - attention_context: {
                    'activated_neurons': [neuron_ids],
                    'relevance_scores': [scores],
                    'market_context': str,
                  }

        Returns:
            Dict with update statistics
        """
        # Validate input
        if not trade_result.get('attention_context'):
            logger.debug("⚠️ No attention context in trade result - skipping RL")
            return {"status": "skipped", "reason": "no_attention_context"}

        pnl = trade_result.get('pnl', 0)
        is_skip_learning = trade_result.get('is_skip_learning', False)

        # Handle skip learning differently
        if is_skip_learning and not self.config.get('skip_learning_enabled', True):
            logger.debug("⚠️ Skip learning disabled - skipping update")
            return {"status": "skipped", "reason": "skip_learning_disabled"}

        # Scale PnL for skip learning (less aggressive)
        if is_skip_learning:
            pnl = pnl * self.config.get('skip_update_scale', 0.6)

        # Filter out small trades
        if abs(pnl) < self.config['min_pnl_for_update']:
            logger.debug(f"⚠️ PnL ${pnl:.2f} below threshold - skipping RL")
            return {"status": "skipped", "reason": "pnl_too_small"}

        # Update statistics
        self.stats.total_trades_processed += 1
        if pnl > 0:
            self.stats.winning_trades += 1
        else:
            self.stats.losing_trades += 1

        # Normalize PnL to [-1, 1] range
        pnl_normalized = self._normalize_pnl(pnl)

        # Extract attention context
        attention_ctx = trade_result['attention_context']
        activated_neurons = attention_ctx.get('activated_neurons', [])
        relevance_scores = attention_ctx.get('relevance_scores', [])

        if not activated_neurons:
            return {"status": "skipped", "reason": "no_activated_neurons"}

        # Limit updates for safety
        max_updates = self.config['max_updates_per_trade']
        activated_neurons = activated_neurons[:max_updates]
        relevance_scores = relevance_scores[:max_updates]

        # Update neurons
        update_results = self._update_neurons(
            activated_neurons,
            relevance_scores,
            pnl_normalized
        )

        # Update synapses (Hebbian learning)
        synapse_results = {}
        if self.config['enable_hebbian'] and len(activated_neurons) > 1:
            synapse_results = self._update_synapses(
                activated_neurons,
                pnl_normalized
            )

        # Update timestamp
        self.stats.last_update_time = time.time()

        # Log summary
        direction = "📈" if pnl > 0 else "📉"
        logger.info(
            f"{direction} RL Update: PnL ${pnl:.2f} → "
            f"{update_results['neurons_updated']} neurons "
            f"({update_results['reinforced']}↑ {update_results['weakened']}↓)"
        )

        if synapse_results:
            logger.info(
                f"   🔗 Synapses: {synapse_results['updated']} updated, "
                f"{synapse_results['created']} created"
            )

        return {
            "status": "success",
            "pnl": pnl,
            "pnl_normalized": pnl_normalized,
            "neuron_updates": update_results,
            "synapse_updates": synapse_results,
        }

    def _normalize_pnl(self, pnl: float) -> float:
        """Normalize PnL to [-1, 1] range"""
        normalized = pnl / self.config['pnl_scale']
        clipped = np.clip(normalized, -self.config['pnl_clip'], self.config['pnl_clip'])
        return float(clipped / self.config['pnl_clip'])  # Scale to [-1, 1]

    def _update_neurons(
        self,
        neuron_ids: List[str],
        relevance_scores: List[float],
        pnl_normalized: float
    ) -> Dict[str, int]:
        """
        Update neuron confidence based on trade result

        Args:
            neuron_ids: List of activated neuron IDs
            relevance_scores: Corresponding relevance scores
            pnl_normalized: Normalized PnL in [-1, 1]

        Returns:
            Dict with update counts
        """
        neurons_updated = 0
        reinforced = 0
        weakened = 0
        confidence_deltas = []

        for neuron_id, relevance in zip(neuron_ids, relevance_scores):
            # Skip low-relevance neurons
            if relevance < self.config['relevance_threshold']:
                continue

            neuron = self.fabric.get_neuron(neuron_id)
            if not neuron or not neuron.is_alive:
                continue

            # Calculate update magnitude
            # Higher relevance = stronger update
            update_magnitude = (
                pnl_normalized *
                relevance *
                self.config['confidence_update_rate']
            )

            # Update confidence
            old_confidence = neuron.confidence
            new_confidence = old_confidence + update_magnitude
            new_confidence = np.clip(
                new_confidence,
                self.config['confidence_min'],
                self.config['confidence_max']
            )

            neuron.confidence = new_confidence

            # Track statistics
            neurons_updated += 1
            confidence_deltas.append(abs(update_magnitude))

            if update_magnitude > 0:
                reinforced += 1
            else:
                weakened += 1

            # Log significant changes
            if abs(update_magnitude) > 0.01:
                logger.debug(
                    f"   {'↑' if update_magnitude > 0 else '↓'} "
                    f"Neuron {neuron_id[:8]}: "
                    f"confidence {old_confidence:.3f} → {new_confidence:.3f} "
                    f"(Δ{update_magnitude:+.3f})"
                )

        # Update global statistics
        self.stats.total_neuron_updates += neurons_updated
        self.stats.total_confidence_increased += reinforced
        self.stats.total_confidence_decreased += weakened

        if confidence_deltas:
            self.stats.avg_confidence_delta.extend(confidence_deltas)

        return {
            "neurons_updated": neurons_updated,
            "reinforced": reinforced,
            "weakened": weakened,
            "avg_delta": np.mean(confidence_deltas) if confidence_deltas else 0.0,
        }

    def _update_synapses(
        self,
        neuron_ids: List[str],
        pnl_normalized: float
    ) -> Dict[str, int]:
        """
        Update synapses between co-activated neurons (Hebbian learning)

        "Neurons that fire together, wire together"

        Args:
            neuron_ids: List of activated neuron IDs
            pnl_normalized: Normalized PnL in [-1, 1]

        Returns:
            Dict with synapse update counts
        """
        synapses_updated = 0
        synapses_created = 0
        synapse_deltas = []

        # Update magnitude
        update_magnitude = pnl_normalized * self.config['synapse_update_rate']

        # Update all pairs of co-activated neurons
        for i, neuron_i in enumerate(neuron_ids[:10]):  # Limit to top 10 for performance
            for neuron_j in neuron_ids[i+1:i+6]:  # Limit connections per neuron

                # Try to get existing synapse
                synapse = self._get_synapse_between(neuron_i, neuron_j)

                if synapse:
                    # Update existing synapse
                    old_weight = synapse.weight
                    new_weight = old_weight + update_magnitude
                    new_weight = np.clip(
                        new_weight,
                        self.config['synapse_min'],
                        self.config['synapse_max']
                    )

                    synapse.weight = new_weight
                    synapses_updated += 1
                    synapse_deltas.append(abs(update_magnitude))

                    logger.debug(
                        f"   🔗 Synapse {neuron_i[:8]}→{neuron_j[:8]}: "
                        f"weight {old_weight:.3f} → {new_weight:.3f}"
                    )

                elif pnl_normalized > 0:
                    # Create new synapse only for winning trades
                    try:
                        self.fabric.create_synapse(
                            source_id=neuron_i,
                            target_id=neuron_j,
                            weight=0.3,  # Initial weight
                            synapse_type="hebbian_rl"
                        )
                        synapses_created += 1
                        logger.debug(
                            f"   ✨ Created synapse {neuron_i[:8]}→{neuron_j[:8]} "
                            f"(weight: 0.3)"
                        )
                    except Exception as e:
                        logger.debug(f"   ⚠️ Failed to create synapse: {e}")

        # Update global statistics
        self.stats.total_synapse_updates += synapses_updated
        self.stats.total_synapses_created += synapses_created

        if synapse_deltas:
            self.stats.avg_synapse_delta.extend(synapse_deltas)

        return {
            "updated": synapses_updated,
            "created": synapses_created,
            "avg_delta": np.mean(synapse_deltas) if synapse_deltas else 0.0,
        }

    def _get_synapse_between(self, source_id: str, target_id: str):
        """Get synapse between two neurons (if exists)"""
        # Check source → target
        outgoing = self.fabric._outgoing.get(source_id, [])
        for syn_id in outgoing:
            synapse = self.fabric._synapses.get(syn_id)
            if synapse and synapse.target_id == target_id:
                return synapse

        # Check target → source (bidirectional)
        outgoing = self.fabric._outgoing.get(target_id, [])
        for syn_id in outgoing:
            synapse = self.fabric._synapses.get(syn_id)
            if synapse and synapse.target_id == source_id:
                return synapse

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get RL statistics"""
        avg_confidence_delta = (
            np.mean(self.stats.avg_confidence_delta[-100:])
            if self.stats.avg_confidence_delta else 0.0
        )

        avg_synapse_delta = (
            np.mean(self.stats.avg_synapse_delta[-100:])
            if self.stats.avg_synapse_delta else 0.0
        )

        total_trades = self.stats.total_trades_processed
        win_rate = (
            self.stats.winning_trades / total_trades
            if total_trades > 0 else 0.0
        )

        return {
            "total_trades_processed": total_trades,
            "winning_trades": self.stats.winning_trades,
            "losing_trades": self.stats.losing_trades,
            "win_rate": f"{win_rate:.1%}",

            "total_neuron_updates": self.stats.total_neuron_updates,
            "confidence_increased": self.stats.total_confidence_increased,
            "confidence_decreased": self.stats.total_confidence_decreased,
            "avg_confidence_delta": f"{avg_confidence_delta:.4f}",

            "total_synapse_updates": self.stats.total_synapse_updates,
            "synapses_created": self.stats.total_synapses_created,
            "avg_synapse_delta": f"{avg_synapse_delta:.4f}",

            "last_update_time": self.stats.last_update_time,
        }

    def log_stats(self):
        """Log statistics summary"""
        stats = self.get_stats()

        logger.info("=" * 80)
        logger.info("📊 SIMPLE RL STATISTICS")
        logger.info("=" * 80)
        logger.info(f"   Trades processed: {stats['total_trades_processed']}")
        logger.info(f"   Win rate: {stats['win_rate']}")
        logger.info("")
        logger.info(f"   Neuron updates: {stats['total_neuron_updates']}")
        logger.info(f"     Reinforced: {stats['confidence_increased']}")
        logger.info(f"     Weakened: {stats['confidence_decreased']}")
        logger.info(f"     Avg delta: {stats['avg_confidence_delta']}")
        logger.info("")
        logger.info(f"   Synapse updates: {stats['total_synapse_updates']}")
        logger.info(f"   Synapses created: {stats['synapses_created']}")
        logger.info(f"     Avg delta: {stats['avg_synapse_delta']}")
        logger.info("=" * 80)


# ============================================================
#  Singleton (Optional)
# ============================================================

_rl_instance: Optional[SimpleAttentionRL] = None

def get_simple_rl(fabric=None, config=None) -> SimpleAttentionRL:
    """Get singleton RL instance"""
    global _rl_instance
    if _rl_instance is None:
        if fabric is None:
            from unified_core.core.neuron_fabric import get_neuron_fabric
            fabric = get_neuron_fabric()
        _rl_instance = SimpleAttentionRL(fabric, config)
    return _rl_instance
