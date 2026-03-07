#!/usr/bin/env python3
"""
Reinforcement Learning Safeguards
==================================

Protects against neuron inflation and overfitting in high-frequency learning.

4 Critical Safeguards:
1. Warm-up Period: Gradual rate increase over first 2 days
2. Batch Updates: Accumulate contexts, update in batches
3. Rate Limiting: Cap skip evaluations per day
4. Dedup/Cooldown: Prevent duplicate learning from same symbol

Usage:
    safeguards = RLSafeguards(config)

    # Warm-up: Get current update rates
    rates = safeguards.get_warmup_rates()
    rl.config['confidence_update_rate'] = rates['confidence']

    # Batch: Accumulate contexts
    safeguards.add_context(context)
    if safeguards.should_process_batch():
        batch = safeguards.get_batch()
        # Process batch...

    # Rate limit: Check before skip evaluation
    if safeguards.can_evaluate_skip():
        # Evaluate skip...

    # Dedup: Check before logging context
    if safeguards.can_log_context(symbol):
        # Log context...
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger("unified_core.core.rl_safeguards")


# ============================================================
#  Configuration
# ============================================================

DEFAULT_SAFEGUARD_CONFIG = {
    # Warm-up period (gradual rate increase)
    "warmup_enabled": True,
    "warmup_duration_hours": 48,  # 2 days
    "warmup_start_rate_scale": 0.2,  # Start at 20% of normal rate
    "warmup_end_rate_scale": 1.0,    # End at 100% of normal rate

    # Batch updates
    "batch_enabled": True,
    "batch_size_min": 50,   # Min contexts before processing
    "batch_size_max": 200,  # Max contexts before forced processing
    "batch_timeout_minutes": 60,  # Process after 1 hour regardless

    # Skip evaluation rate limiting
    "skip_rate_limit_enabled": True,
    "max_skip_evaluations_per_hour": 50,  # Cap at 50 skips/hour
    "max_skip_evaluations_per_day": 500,  # Cap at 500 skips/day
    "skip_random_sample_rate": 0.3,  # Sample 30% of skips if over limit

    # Context deduplication and cooldown
    "dedup_enabled": True,
    "context_cooldown_minutes": 15,  # 15min cooldown per symbol
    "max_contexts_per_symbol_per_hour": 12,  # Max 12 contexts/symbol/hour
}


# ============================================================
#  Data Classes
# ============================================================

@dataclass
class WarmupState:
    """Track warm-up progress"""
    start_time: float = field(default_factory=time.time)
    duration_hours: float = 48.0
    start_scale: float = 0.2
    end_scale: float = 1.0

    def get_current_scale(self) -> float:
        """Get current rate scale based on elapsed time"""
        elapsed_hours = (time.time() - self.start_time) / 3600

        if elapsed_hours >= self.duration_hours:
            return self.end_scale  # Warm-up complete

        # Linear interpolation
        progress = elapsed_hours / self.duration_hours
        scale = self.start_scale + (self.end_scale - self.start_scale) * progress

        return scale

    def is_complete(self) -> bool:
        """Check if warm-up is complete"""
        elapsed_hours = (time.time() - self.start_time) / 3600
        return elapsed_hours >= self.duration_hours


@dataclass
class BatchState:
    """Track batch accumulation"""
    contexts: List[Any] = field(default_factory=list)
    last_process_time: float = field(default_factory=time.time)
    total_batches_processed: int = 0

    def add(self, context: Any):
        """Add context to batch"""
        self.contexts.append(context)

    def should_process(self, min_size: int, max_size: int, timeout_minutes: int) -> bool:
        """Check if batch should be processed"""
        # Force process if max size reached
        if len(self.contexts) >= max_size:
            return True

        # Process if min size reached and timeout expired
        if len(self.contexts) >= min_size:
            elapsed_minutes = (time.time() - self.last_process_time) / 60
            if elapsed_minutes >= timeout_minutes:
                return True

        return False

    def get_batch(self) -> List[Any]:
        """Get current batch and clear"""
        batch = self.contexts.copy()
        self.contexts.clear()
        self.last_process_time = time.time()
        self.total_batches_processed += 1
        return batch


@dataclass
class RateLimitState:
    """Track rate limits"""
    skip_evaluations_this_hour: int = 0
    skip_evaluations_this_day: int = 0

    hour_start: float = field(default_factory=time.time)
    day_start: float = field(default_factory=time.time)

    def increment_skip(self):
        """Increment skip counter"""
        self.skip_evaluations_this_hour += 1
        self.skip_evaluations_this_day += 1

    def check_and_reset(self):
        """Check if hour/day expired and reset counters"""
        now = time.time()

        # Check hour
        if (now - self.hour_start) >= 3600:
            self.skip_evaluations_this_hour = 0
            self.hour_start = now

        # Check day
        if (now - self.day_start) >= 86400:
            self.skip_evaluations_this_day = 0
            self.day_start = now

    def can_evaluate_skip(self, max_per_hour: int, max_per_day: int) -> bool:
        """Check if skip evaluation is allowed"""
        self.check_and_reset()

        if self.skip_evaluations_this_hour >= max_per_hour:
            return False

        if self.skip_evaluations_this_day >= max_per_day:
            return False

        return True


@dataclass
class DedupState:
    """Track context deduplication"""
    symbol_last_context: Dict[str, float] = field(default_factory=dict)
    symbol_contexts_this_hour: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    hour_start: float = field(default_factory=time.time)

    def can_log_context(
        self,
        symbol: str,
        cooldown_minutes: int,
        max_per_hour: int
    ) -> bool:
        """Check if context can be logged for this symbol"""
        now = time.time()

        # Reset hourly counters if hour expired
        if (now - self.hour_start) >= 3600:
            self.symbol_contexts_this_hour.clear()
            self.hour_start = now

        # Check cooldown
        last_time = self.symbol_last_context.get(symbol, 0)
        if (now - last_time) < (cooldown_minutes * 60):
            return False

        # Check hourly limit
        if self.symbol_contexts_this_hour[symbol] >= max_per_hour:
            return False

        return True

    def mark_logged(self, symbol: str):
        """Mark context as logged"""
        self.symbol_last_context[symbol] = time.time()
        self.symbol_contexts_this_hour[symbol] += 1


# ============================================================
#  Safeguards Manager
# ============================================================

class RLSafeguards:
    """
    Manages all RL safeguards to prevent overfitting and instability
    """

    def __init__(self, config: Dict = None):
        """
        Initialize safeguards

        Args:
            config: Safeguard configuration
        """
        self.config = {**DEFAULT_SAFEGUARD_CONFIG, **(config or {})}

        # State tracking
        self.warmup_state = WarmupState(
            duration_hours=self.config['warmup_duration_hours'],
            start_scale=self.config['warmup_start_rate_scale'],
            end_scale=self.config['warmup_end_rate_scale']
        )

        self.batch_state = BatchState()
        self.rate_limit_state = RateLimitState()
        self.dedup_state = DedupState()

        # Statistics
        self.contexts_blocked_by_cooldown = 0
        self.contexts_blocked_by_rate_limit = 0
        self.skips_blocked_by_rate_limit = 0
        self.batches_processed = 0

        logger.info("🛡️ RL Safeguards initialized")
        logger.info(f"   Warm-up: {self.config['warmup_enabled']} ({self.config['warmup_duration_hours']}h)")
        logger.info(f"   Batch updates: {self.config['batch_enabled']} ({self.config['batch_size_min']}-{self.config['batch_size_max']})")
        logger.info(f"   Skip rate limit: {self.config['skip_rate_limit_enabled']} ({self.config['max_skip_evaluations_per_hour']}/hour)")
        logger.info(f"   Context dedup: {self.config['dedup_enabled']} ({self.config['context_cooldown_minutes']}min cooldown)")

    # ========================================
    # Warm-up Period
    # ========================================

    def get_warmup_rates(self, base_rates: Dict[str, float] = None) -> Dict[str, float]:
        """
        Get current update rates based on warm-up progress

        Args:
            base_rates: Base rates to scale (defaults to simple_attention_rl.DEFAULT_CONFIG)

        Returns:
            Dict with scaled rates
        """
        if not self.config['warmup_enabled']:
            return base_rates or {}

        scale = self.warmup_state.get_current_scale()

        if base_rates:
            return {
                key: value * scale
                for key, value in base_rates.items()
            }

        # Default rates from simple_attention_rl
        from unified_core.core.simple_attention_rl import DEFAULT_CONFIG as RL_CONFIG

        return {
            'confidence_update_rate': RL_CONFIG['confidence_update_rate'] * scale,
            'synapse_update_rate': RL_CONFIG['synapse_update_rate'] * scale,
        }

    def is_warmup_complete(self) -> bool:
        """Check if warm-up period is complete"""
        return self.warmup_state.is_complete()

    # ========================================
    # Batch Updates
    # ========================================

    def add_context(self, context: Any):
        """Add context to batch"""
        if not self.config['batch_enabled']:
            return

        self.batch_state.add(context)

    def should_process_batch(self) -> bool:
        """Check if batch should be processed"""
        if not self.config['batch_enabled']:
            return True  # Process immediately if batching disabled

        return self.batch_state.should_process(
            min_size=self.config['batch_size_min'],
            max_size=self.config['batch_size_max'],
            timeout_minutes=self.config['batch_timeout_minutes']
        )

    def get_batch(self) -> List[Any]:
        """Get current batch and clear"""
        batch = self.batch_state.get_batch()
        self.batches_processed += 1
        return batch

    def get_batch_size(self) -> int:
        """Get current batch size"""
        return len(self.batch_state.contexts)

    # ========================================
    # Skip Evaluation Rate Limiting
    # ========================================

    def can_evaluate_skip(self) -> bool:
        """Check if skip evaluation is allowed"""
        if not self.config['skip_rate_limit_enabled']:
            return True

        can_evaluate = self.rate_limit_state.can_evaluate_skip(
            max_per_hour=self.config['max_skip_evaluations_per_hour'],
            max_per_day=self.config['max_skip_evaluations_per_day']
        )

        if can_evaluate:
            self.rate_limit_state.increment_skip()
        else:
            self.skips_blocked_by_rate_limit += 1

        return can_evaluate

    def should_sample_skip(self) -> bool:
        """
        Check if skip should be sampled (if over rate limit)

        Uses random sampling to still learn from some skips
        even when over rate limit.
        """
        if not self.config['skip_rate_limit_enabled']:
            return True

        import random
        return random.random() < self.config['skip_random_sample_rate']

    # ========================================
    # Context Deduplication
    # ========================================

    def can_log_context(self, symbol: str) -> bool:
        """Check if context can be logged for this symbol"""
        if not self.config['dedup_enabled']:
            return True

        can_log = self.dedup_state.can_log_context(
            symbol=symbol,
            cooldown_minutes=self.config['context_cooldown_minutes'],
            max_per_hour=self.config['max_contexts_per_symbol_per_hour']
        )

        if not can_log:
            self.contexts_blocked_by_cooldown += 1
            return False

        self.dedup_state.mark_logged(symbol)
        return True

    # ========================================
    # Statistics
    # ========================================

    def get_stats(self) -> Dict[str, Any]:
        """Get safeguard statistics"""
        warmup_scale = self.warmup_state.get_current_scale()
        warmup_complete = self.warmup_state.is_complete()

        return {
            'warmup': {
                'enabled': self.config['warmup_enabled'],
                'complete': warmup_complete,
                'current_scale': f"{warmup_scale:.2f}",
                'elapsed_hours': f"{(time.time() - self.warmup_state.start_time) / 3600:.1f}h",
            },
            'batch': {
                'enabled': self.config['batch_enabled'],
                'current_size': len(self.batch_state.contexts),
                'batches_processed': self.batches_processed,
            },
            'rate_limit': {
                'enabled': self.config['skip_rate_limit_enabled'],
                'skips_this_hour': self.rate_limit_state.skip_evaluations_this_hour,
                'skips_this_day': self.rate_limit_state.skip_evaluations_this_day,
                'skips_blocked': self.skips_blocked_by_rate_limit,
            },
            'dedup': {
                'enabled': self.config['dedup_enabled'],
                'contexts_blocked': self.contexts_blocked_by_cooldown,
                'symbols_tracked': len(self.dedup_state.symbol_last_context),
            }
        }

    def log_stats(self):
        """Log statistics summary"""
        stats = self.get_stats()

        logger.info("=" * 80)
        logger.info("🛡️ RL SAFEGUARDS STATISTICS")
        logger.info("=" * 80)

        # Warm-up
        logger.info(f"🔥 Warm-up:")
        logger.info(f"   Enabled: {stats['warmup']['enabled']}")
        if stats['warmup']['enabled']:
            logger.info(f"   Complete: {stats['warmup']['complete']}")
            logger.info(f"   Current scale: {stats['warmup']['current_scale']}")
            logger.info(f"   Elapsed: {stats['warmup']['elapsed_hours']}")

        # Batch
        logger.info(f"")
        logger.info(f"📦 Batch Updates:")
        logger.info(f"   Enabled: {stats['batch']['enabled']}")
        if stats['batch']['enabled']:
            logger.info(f"   Current batch: {stats['batch']['current_size']}")
            logger.info(f"   Batches processed: {stats['batch']['batches_processed']}")

        # Rate limit
        logger.info(f"")
        logger.info(f"⏱️ Rate Limiting:")
        logger.info(f"   Enabled: {stats['rate_limit']['enabled']}")
        if stats['rate_limit']['enabled']:
            logger.info(f"   Skips this hour: {stats['rate_limit']['skips_this_hour']}")
            logger.info(f"   Skips this day: {stats['rate_limit']['skips_this_day']}")
            logger.info(f"   Skips blocked: {stats['rate_limit']['skips_blocked']}")

        # Dedup
        logger.info(f"")
        logger.info(f"🔄 Deduplication:")
        logger.info(f"   Enabled: {stats['dedup']['enabled']}")
        if stats['dedup']['enabled']:
            logger.info(f"   Contexts blocked: {stats['dedup']['contexts_blocked']}")
            logger.info(f"   Symbols tracked: {stats['dedup']['symbols_tracked']}")

        logger.info("=" * 80)


# ============================================================
#  Singleton (Optional)
# ============================================================

_safeguards_instance: Optional[RLSafeguards] = None

def get_rl_safeguards(config: Dict = None) -> RLSafeguards:
    """Get singleton safeguards instance"""
    global _safeguards_instance
    if _safeguards_instance is None:
        _safeguards_instance = RLSafeguards(config)
    return _safeguards_instance
