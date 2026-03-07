"""
Evolution Engine Configuration v4.0

Centralized configuration for the entire evolution pipeline.
All magic numbers, thresholds, and constants live here.

To override, set environment variables with prefix NOOGH_EVO_
"""
import os
from pathlib import Path

def _env(key: str, default, cast=None):
    """Read from env with optional casting."""
    val = os.getenv(f"NOOGH_EVO_{key}", None)
    if val is None:
        return default
    if cast:
        return cast(val)
    return val


# ═══════════════════════════════════════════════════════════════
# Risk & Approval Thresholds
# ═══════════════════════════════════════════════════════════════

# Maximum risk score for auto-execution (bypasses manual review)
AUTO_EXECUTE_RISK_THRESHOLD = _env("AUTO_EXECUTE_RISK", 75, int)

# Maximum risk score for agent proposals (higher because canary catches issues)
AGENT_RISK_THRESHOLD = _env("AGENT_RISK", 90, int)

# Risk threshold below which proposals are auto-approved
LOW_RISK_THRESHOLD = _env("LOW_RISK", 30, int)


# ═══════════════════════════════════════════════════════════════
# Rate Limits
# ═══════════════════════════════════════════════════════════════

# Maximum proposals per hour
MAX_PROPOSALS_PER_HOUR = _env("MAX_PROPOSALS_HOUR", 20, int)

# Maximum executions per hour  
MAX_EXECUTIONS_PER_HOUR = _env("MAX_EXECUTIONS_HOUR", 10, int)

# Maximum total proposals before kill switch
MAX_TOTAL_PROPOSALS = _env("MAX_TOTAL", 1000, int)


# ═══════════════════════════════════════════════════════════════
# Ledger Thresholds
# ═══════════════════════════════════════════════════════════════

# General risk threshold — reject proposals above this score (raised to 90)
RISK_THRESHOLD = _env("RISK_THRESHOLD", 90, int)

# Cooldown after execution failure (seconds) - reduced from 300 to 30
FAILURE_COOLDOWN_SECONDS = _env("FAILURE_COOLDOWN", 30, int)


# ═══════════════════════════════════════════════════════════════
# Per-Type Risk Thresholds (controller)
# ═══════════════════════════════════════════════════════════════

# Max risk for auto-executing config proposals
CONFIG_RISK_THRESHOLD = _env("CONFIG_RISK", 75, int)

# Max risk for auto-executing policy proposals
POLICY_RISK_THRESHOLD = _env("POLICY_RISK", 65, int)

# Max risk for auto-executing code proposals
CODE_RISK_THRESHOLD = _env("CODE_RISK", 75, int)

# Sandbox timeout for canary/execution (seconds)
SANDBOX_TIMEOUT = _env("SANDBOX_TIMEOUT", 10.0, float)


# ═══════════════════════════════════════════════════════════════
# Brain Refactoring
# ═══════════════════════════════════════════════════════════════

# Cooldown before re-analyzing same function (seconds)
REFACTOR_COOLDOWN_SECONDS = _env("REFACTOR_COOLDOWN", 3600, int)

# Maximum tokens for Brain completion (must be < model context - prompt tokens)
BRAIN_MAX_TOKENS = _env("BRAIN_MAX_TOKENS", 4096, int)

# Timeout for Brain HTTP requests (seconds)
BRAIN_REQUEST_TIMEOUT = _env("BRAIN_TIMEOUT", 120, int)

# Maximum concurrent refactor requests
BRAIN_MAX_CONCURRENT = _env("BRAIN_MAX_CONCURRENT", 2, int)

# Maximum issues to process per cycle
BRAIN_MAX_ISSUES_PER_CYCLE = _env("BRAIN_MAX_ISSUES", 2, int)

# Maximum extraction retries for truncated/broken LLM responses
MAX_EXTRACTION_RETRIES = _env("MAX_EXTRACTION_RETRIES", 2, int)

# Project root directory (auto-detected, overridable via env)
PROJECT_ROOT = _env("PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))

# Maximum diff size in bytes (reject enormous diffs)
MAX_DIFF_SIZE = _env("MAX_DIFF_SIZE", 50000, int)

# Maximum function length in lines (flag overly long functions)
MAX_FUNCTION_LINES = _env("MAX_FUNCTION_LINES", 200, int)


# ═══════════════════════════════════════════════════════════════
# Deduplication
# ═══════════════════════════════════════════════════════════════

# Window for proposal content dedup (seconds)
PROPOSAL_DEDUP_WINDOW = _env("DEDUP_WINDOW", 900, int)


# ═══════════════════════════════════════════════════════════════
# Kill Switch
# ═══════════════════════════════════════════════════════════════

# Maximum failures in 24h before kill switch activates (raised from 15 to 100)
KILL_SWITCH_FAILURE_THRESHOLD = _env("KILL_FAILURES", 100, int)

# Kill switch cooldown (seconds) - keep at 24h
KILL_SWITCH_COOLDOWN = _env("KILL_COOLDOWN", 86400, int)


# ═══════════════════════════════════════════════════════════════
# Core Interface Lock
# Files that Brain cannot modify without manual review
# ═══════════════════════════════════════════════════════════════

_DEFAULT_LOCKED_FILES = (
    "orchestrator.py,module_interface.py,governor.py,meta_governor.py,"
    "decision_governor.py,controller.py,ledger.py,brain_refactor.py,"
    "evolution_config.py,agent_daemon.py,policy_gate.py,hmac_logger.py"
)
_locked_raw = _env("CORE_LOCKED_FILES", _DEFAULT_LOCKED_FILES)
CORE_INTERFACE_LOCKED_FILES = set(f.strip() for f in _locked_raw.split(",") if f.strip())


# ═══════════════════════════════════════════════════════════════
# Canary Validation Phases
# ═══════════════════════════════════════════════════════════════

# Enable runtime import test (Phase 4) — can be disabled for safety
CANARY_ENABLE_IMPORT_TEST = _env("CANARY_IMPORT_TEST", True, lambda v: v.lower() == 'true')

# Enable AST Emission Guard (Phase -1)
CANARY_ENABLE_EMISSION_GUARD = _env("CANARY_EMISSION_GUARD", True, lambda v: v.lower() == 'true')

# Enable Core Interface Lock (Phase -2)
CANARY_ENABLE_CORE_LOCK = _env("CANARY_CORE_LOCK", True, lambda v: v.lower() == 'true')


# ═══════════════════════════════════════════════════════════════
# Distillation
# ═══════════════════════════════════════════════════════════════

# Minimum quality threshold for distillation trajectories
DISTILLATION_MIN_QUALITY = _env("DISTILL_MIN_QUALITY", 0.6, float)

# Maximum trajectories to keep
DISTILLATION_MAX_TRAJECTORIES = _env("DISTILL_MAX_TRAJ", 5000, int)


# ═══════════════════════════════════════════════════════════════
# Circuit Breaker (Neural Bridge)
# ═══════════════════════════════════════════════════════════════

# Consecutive failures before circuit opens
CB_FAILURE_THRESHOLD = _env("CB_FAILURES", 5, int)

# Seconds before attempting recovery (half-open)
CB_RECOVERY_TIMEOUT = _env("CB_RECOVERY", 60, int)


# ═══════════════════════════════════════════════════════════════
# Neural Bridge
# ═══════════════════════════════════════════════════════════════

# Max retries per call
NEURAL_MAX_RETRIES = _env("NEURAL_MAX_RETRIES", 2, int)

# vLLM temperature for generation
VLLM_TEMPERATURE = _env("VLLM_TEMPERATURE", 0.7, float)

# Neural result cache TTL (seconds, 0 = disabled)
NEURAL_CACHE_TTL = _env("NEURAL_CACHE_TTL", 60, int)
