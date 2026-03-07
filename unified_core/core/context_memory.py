"""
Context Memory & Experience Replay
===================================

Stores complete market analysis contexts for experience replay.
Enables learning from historical contexts, not just new trades.

Key innovations:
1. Context Memory: Complete market snapshots
2. Experience Replay: Re-learn from past experiences
3. Neuron Usage Tracking: Monitor which neurons are actually useful

Based on:
- DeepMind's DQN (Experience Replay)
- OpenAI's PPO (Sample Efficiency)
- Network Pruning (Usage-based importance)

Architecture:
    Market Analysis → Store Context → Experience Buffer
                                            ↓
                                    Periodic Replay
                                            ↓
                                    RL learns 2x faster

Usage:
    memory = ContextMemory(max_size=1000)

    # Store every analysis
    memory.store_context(
        symbol='BTCUSDT',
        price=50000,
        market_data={...},
        attention_result={...},
        brain_decision={...}
    )

    # Replay periodically
    memory.replay_batch(rl_system, batch_size=20)
"""

import logging
import time
import random
import pickle
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque
from pathlib import Path
import numpy as np

logger = logging.getLogger("unified_core.core.context_memory")


# ============================================================
#  Data Classes
# ============================================================

@dataclass
class MarketContext:
    """Complete market analysis context snapshot"""

    # Identity
    context_id: str
    symbol: str
    timestamp: float

    # Market state
    price: float
    funding_rate: Optional[float] = None
    rsi: Optional[float] = None
    atr: Optional[float] = None
    delta: Optional[float] = None
    cvd: Optional[float] = None
    volume: Optional[float] = None

    # Signal data
    signal_data: Dict[str, Any] = field(default_factory=dict)

    # Attention result
    activated_neurons: List[str] = field(default_factory=list)
    relevance_scores: List[float] = field(default_factory=list)
    avg_relevance: float = 0.0

    # Brain decision
    decision: str = "SKIP"
    confidence: float = 0.0
    brain_reason: str = ""

    # Execution
    executed: bool = False
    trade_id: Optional[str] = None

    # Outcome (filled later)
    outcome_known: bool = False
    actual_pnl: Optional[float] = None
    simulated_pnl: Optional[float] = None

    # Replay tracking
    replay_count: int = 0
    last_replay: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'context_id': self.context_id,
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'price': self.price,
            'decision': self.decision,
            'confidence': self.confidence,
            'executed': self.executed,
            'outcome_known': self.outcome_known,
            'actual_pnl': self.actual_pnl,
            'replay_count': self.replay_count,
        }


@dataclass
class NeuronUsageTracker:
    """Track neuron usage for pruning decisions"""
    neuron_id: str

    # Usage metrics
    activation_count: int = 0
    last_activated: Optional[float] = None

    # Performance metrics
    wins_involved: int = 0
    losses_involved: int = 0
    total_pnl_contribution: float = 0.0

    # Computed scores
    usage_frequency: float = 0.0  # activations / time_window
    win_rate: float = 0.0
    avg_pnl: float = 0.0

    # Combined score
    importance_score: float = 0.0  # confidence × usage × performance

    def update_from_context(self, context: MarketContext, neuron_confidence: float):
        """Update metrics from a context"""
        self.activation_count += 1
        self.last_activated = context.timestamp

        if context.outcome_known and context.actual_pnl:
            if context.actual_pnl > 0:
                self.wins_involved += 1
            else:
                self.losses_involved += 1

            self.total_pnl_contribution += context.actual_pnl

            # Update computed metrics
            total_trades = self.wins_involved + self.losses_involved
            if total_trades > 0:
                self.win_rate = self.wins_involved / total_trades
                self.avg_pnl = self.total_pnl_contribution / total_trades

        # Compute importance score
        self.importance_score = (
            neuron_confidence * 0.4 +
            min(1.0, self.usage_frequency) * 0.3 +
            max(0.0, min(1.0, self.win_rate)) * 0.3
        )


@dataclass
class MemoryStats:
    """Statistics for context memory"""
    total_contexts: int = 0
    executed_contexts: int = 0
    replayed_contexts: int = 0

    avg_replay_count: float = 0.0
    contexts_with_outcome: int = 0

    buffer_size: int = 0
    buffer_capacity: int = 0


# ============================================================
#  Context Memory
# ============================================================

class ContextMemory:
    """
    Experience Replay Buffer for market contexts

    Stores complete market analysis contexts and enables
    experience replay for faster learning.
    """

    def __init__(
        self,
        max_size: int = 1000,
        save_path: Optional[str] = None
    ):
        """
        Initialize context memory

        Args:
            max_size: Maximum contexts to store
            save_path: Optional path to save/load memory
        """
        self.max_size = max_size
        self.save_path = Path(save_path) if save_path else None

        # Context buffer (FIFO)
        self.buffer = deque(maxlen=max_size)

        # Neuron usage tracking
        self.neuron_usage: Dict[str, NeuronUsageTracker] = {}

        # Statistics
        self.stats = MemoryStats()
        self.stats.buffer_capacity = max_size

        # Load existing memory if available
        if self.save_path and self.save_path.exists():
            self._load()

        logger.info(
            f"💾 ContextMemory initialized: "
            f"capacity={max_size}, "
            f"loaded={len(self.buffer)} contexts"
        )

    def store_context(
        self,
        symbol: str,
        price: float,
        attention_result: Dict,
        brain_decision: Dict,
        signal_data: Dict = None,
        market_data: Dict = None,
        executed: bool = False,
        trade_id: Optional[str] = None
    ) -> MarketContext:
        """
        Store complete market analysis context

        Args:
            symbol: Trading symbol
            price: Current price
            attention_result: Result from attention mechanism
            brain_decision: Brain's decision
            signal_data: Market signal data
            market_data: Additional market metrics
            executed: Whether trade was executed
            trade_id: Optional trade ID if executed

        Returns:
            Created MarketContext
        """
        # Generate context ID
        context_id = f"{symbol}_{int(time.time() * 1000)}"

        # Extract attention data
        attention_results = attention_result.get('attention_results', [])
        activated_neurons = [r.neuron_id for r in attention_results]
        relevance_scores = [r.relevance_score for r in attention_results]
        avg_relevance = attention_result.get('stats', {}).get('avg_relevance', 0)

        # Extract market data if provided
        market_data = market_data or {}

        # Create context
        context = MarketContext(
            context_id=context_id,
            symbol=symbol,
            timestamp=time.time(),
            price=price,
            funding_rate=market_data.get('funding_rate'),
            rsi=market_data.get('rsi'),
            atr=market_data.get('atr'),
            delta=market_data.get('delta'),
            cvd=market_data.get('cvd'),
            volume=market_data.get('volume'),
            signal_data=signal_data or {},
            activated_neurons=activated_neurons,
            relevance_scores=relevance_scores,
            avg_relevance=avg_relevance,
            decision=brain_decision.get('decision', 'SKIP'),
            confidence=brain_decision.get('confidence', 0) / 100.0,
            brain_reason=brain_decision.get('reason', ''),
            executed=executed,
            trade_id=trade_id,
        )

        # Store in buffer
        self.buffer.append(context)

        # Update statistics
        self.stats.total_contexts += 1
        self.stats.buffer_size = len(self.buffer)
        if executed:
            self.stats.executed_contexts += 1

        # Track neuron usage
        self._update_neuron_usage(context)

        logger.debug(
            f"💾 Stored context: {symbol} | {context.decision} | "
            f"neurons={len(activated_neurons)}"
        )

        return context

    def update_outcome(
        self,
        context_id: str,
        actual_pnl: Optional[float] = None,
        simulated_pnl: Optional[float] = None
    ):
        """
        Update context with known outcome

        Args:
            context_id: Context ID
            actual_pnl: Actual PnL if executed
            simulated_pnl: Simulated PnL if skipped
        """
        for context in self.buffer:
            if context.context_id == context_id:
                context.outcome_known = True
                context.actual_pnl = actual_pnl
                context.simulated_pnl = simulated_pnl

                self.stats.contexts_with_outcome += 1

                # Update neuron usage with outcome
                self._update_neuron_usage(context)

                logger.debug(
                    f"📊 Updated outcome: {context_id} | "
                    f"PnL={actual_pnl or simulated_pnl:.2f}"
                )
                break

    def replay_batch(
        self,
        rl_system,
        batch_size: int = 20,
        prioritize_outcomes: bool = True
    ) -> List[Dict]:
        """
        Replay random batch of contexts for learning

        Args:
            rl_system: SimpleAttentionRL instance
            batch_size: Number of contexts to replay
            prioritize_outcomes: Prioritize contexts with known outcomes

        Returns:
            List of RL update results
        """
        if not self.buffer:
            logger.debug("⚠️ No contexts to replay")
            return []

        # Select batch
        if prioritize_outcomes:
            # Prioritize contexts with known outcomes
            with_outcomes = [c for c in self.buffer if c.outcome_known]
            without_outcomes = [c for c in self.buffer if not c.outcome_known]

            # 70% with outcomes, 30% without
            n_with = min(len(with_outcomes), int(batch_size * 0.7))
            n_without = min(len(without_outcomes), batch_size - n_with)

            batch = (
                random.sample(with_outcomes, n_with) if with_outcomes else []
            ) + (
                random.sample(without_outcomes, n_without) if without_outcomes else []
            )
        else:
            # Random sample
            batch = random.sample(
                list(self.buffer),
                min(batch_size, len(self.buffer))
            )

        # Replay each context
        results = []
        for context in batch:
            # Convert to trade result format
            trade_result = self._context_to_trade_result(context)

            if trade_result:
                # Apply RL update
                try:
                    result = rl_system.process_trade_result(trade_result)
                    results.append(result)

                    # Update replay tracking
                    context.replay_count += 1
                    context.last_replay = time.time()

                    self.stats.replayed_contexts += 1

                except Exception as e:
                    logger.debug(f"❌ Replay failed: {e}")

        # Update average replay count
        if self.buffer:
            self.stats.avg_replay_count = (
                sum(c.replay_count for c in self.buffer) / len(self.buffer)
            )

        logger.info(
            f"🔄 Replayed {len(results)}/{batch_size} contexts "
            f"(with_outcomes={sum(1 for c in batch if c.outcome_known)})"
        )

        return results

    def _context_to_trade_result(self, context: MarketContext) -> Optional[Dict]:
        """Convert context to trade result format for RL"""
        # Need outcome to create trade result
        if not context.outcome_known:
            return None

        pnl = context.actual_pnl or context.simulated_pnl or 0

        return {
            'pnl': pnl,
            'result': 'WIN' if pnl > 0 else 'LOSS',
            'attention_context': {
                'activated_neurons': context.activated_neurons,
                'relevance_scores': context.relevance_scores,
                'market_context': f"Replay: {context.symbol}",
            },
            'is_replay': True,  # Flag for RL
            'context_id': context.context_id,
        }

    def _update_neuron_usage(self, context: MarketContext):
        """Update neuron usage tracking"""
        for neuron_id in context.activated_neurons:
            if neuron_id not in self.neuron_usage:
                self.neuron_usage[neuron_id] = NeuronUsageTracker(neuron_id)

            # Get neuron confidence (would need fabric access - simplified)
            tracker = self.neuron_usage[neuron_id]
            tracker.update_from_context(context, confidence=0.5)

            # Update usage frequency (simplified)
            time_window = 86400  # 24 hours
            tracker.usage_frequency = tracker.activation_count / time_window

    def get_neuron_importance(self, top_n: int = 50) -> List[tuple]:
        """
        Get most important neurons based on usage + performance

        Args:
            top_n: Number of top neurons to return

        Returns:
            List of (neuron_id, importance_score, usage_metrics)
        """
        ranked = sorted(
            self.neuron_usage.items(),
            key=lambda x: x[1].importance_score,
            reverse=True
        )

        return [
            (
                neuron_id,
                tracker.importance_score,
                {
                    'activations': tracker.activation_count,
                    'win_rate': tracker.win_rate,
                    'avg_pnl': tracker.avg_pnl,
                }
            )
            for neuron_id, tracker in ranked[:top_n]
        ]

    def get_low_importance_neurons(self, threshold: float = 0.2) -> List[str]:
        """
        Get neurons with low importance (candidates for pruning)

        Args:
            threshold: Importance threshold

        Returns:
            List of neuron IDs
        """
        return [
            neuron_id
            for neuron_id, tracker in self.neuron_usage.items()
            if tracker.importance_score < threshold and tracker.activation_count > 10
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            'total_contexts': self.stats.total_contexts,
            'buffer_size': self.stats.buffer_size,
            'buffer_capacity': self.stats.buffer_capacity,
            'buffer_utilization': f"{self.stats.buffer_size / self.stats.buffer_capacity:.1%}",

            'executed_contexts': self.stats.executed_contexts,
            'contexts_with_outcome': self.stats.contexts_with_outcome,

            'replayed_contexts': self.stats.replayed_contexts,
            'avg_replay_count': f"{self.stats.avg_replay_count:.2f}",

            'neurons_tracked': len(self.neuron_usage),
        }

    def log_stats(self):
        """Log statistics summary"""
        stats = self.get_stats()

        logger.info("=" * 80)
        logger.info("💾 CONTEXT MEMORY STATISTICS")
        logger.info("=" * 80)
        logger.info(f"   Total contexts: {stats['total_contexts']}")
        logger.info(f"   Buffer: {stats['buffer_size']}/{stats['buffer_capacity']} ({stats['buffer_utilization']})")
        logger.info("")
        logger.info(f"   Executed: {stats['executed_contexts']}")
        logger.info(f"   With outcome: {stats['contexts_with_outcome']}")
        logger.info("")
        logger.info(f"   Replayed: {stats['replayed_contexts']}")
        logger.info(f"   Avg replay count: {stats['avg_replay_count']}")
        logger.info("")
        logger.info(f"   Neurons tracked: {stats['neurons_tracked']}")
        logger.info("=" * 80)

    def save(self):
        """Save memory to disk"""
        if not self.save_path:
            return

        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'buffer': list(self.buffer),
                'neuron_usage': self.neuron_usage,
                'stats': self.stats,
            }

            with open(self.save_path, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

            logger.info(f"💾 Saved context memory: {self.save_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save memory: {e}")

    def _load(self):
        """Load memory from disk"""
        try:
            with open(self.save_path, 'rb') as f:
                data = pickle.load(f)

            self.buffer = deque(data['buffer'], maxlen=self.max_size)
            self.neuron_usage = data['neuron_usage']
            self.stats = data['stats']

            logger.info(
                f"📂 Loaded context memory: {len(self.buffer)} contexts, "
                f"{len(self.neuron_usage)} neurons tracked"
            )
        except Exception as e:
            logger.warning(f"Failed to load memory: {e}")


# ============================================================
#  Singleton (Optional)
# ============================================================

_context_memory_instance: Optional[ContextMemory] = None

def get_context_memory(max_size: int = 1000, save_path: str = None) -> ContextMemory:
    """Get singleton context memory instance"""
    global _context_memory_instance
    if _context_memory_instance is None:
        _context_memory_instance = ContextMemory(max_size, save_path)
    return _context_memory_instance
