"""
Security Hardening Module — Input Sanitization, Rate Limiting, Tamper Detection

NOOGH Phase 4 Integration:
1. InputSanitizer: Prevents injection attacks (code injection, path traversal, prompt injection)
2. RateLimiter: Token bucket rate limiting for API calls
3. TamperDetector: SHA-256 integrity verification for NeuronFabric persistence

HONESTY NOTE:
- These protections are advisory and filesystem-based
- A sufficiently motivated attacker with system access can bypass them
- The goal is defense-in-depth, not absolute security
"""

import hashlib
import json
import logging
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("unified_core.integration.security")


# ============================================================
#  1. Input Sanitizer
# ============================================================

class InputSanitizer:
    """
    Sanitize user and system inputs to prevent injection attacks.
    
    Defends against:
    - Code injection (eval, exec, __import__, subprocess)
    - Path traversal (../, /etc/, /proc/)
    - Prompt injection (ignore previous, system prompt override)
    - Excessive input length
    """
    
    # Patterns that should never appear in beliefs, propositions, or queries
    DANGEROUS_PATTERNS = [
        r'__import__\s*\(',
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\bos\.system\s*\(',
        r'\bsubprocess\.',
        r'\bopen\s*\([^)]*["\']w',    # open(..., 'w')
        r'rm\s+-rf\s+/',
        r'\brm\s+/',
        r';\s*(rm|cat|wget|curl)\s',
        r'\|\s*(sh|bash|python)',
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\.\/',
        r'\.\.\\\\',
        r'\/etc\/',
        r'\/proc\/',
        r'\/dev\/',
        r'~\/\.',
    ]
    
    PROMPT_INJECTION_PATTERNS = [
        r'ignore\s+(all\s+)?previous\s+instructions',
        r'forget\s+(everything|all)',
        r'you\s+are\s+now\s+(?:a\s+)?(?:different|new)',
        r'override\s+system\s+prompt',
        r'disregard\s+(?:all\s+)?(?:safety|rules)',
    ]
    
    MAX_INPUT_LENGTH = 10000   # 10KB max for any single input
    MAX_PROPOSITION_LENGTH = 500
    
    def __init__(self):
        self._violations: List[Dict[str, Any]] = []
        self._compiled_dangerous = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
        self._compiled_path = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]
        self._compiled_injection = [re.compile(p, re.IGNORECASE) for p in self.PROMPT_INJECTION_PATTERNS]
    
    def sanitize(self, text: str, context: str = "unknown") -> Tuple[str, List[str]]:
        """
        Sanitize input text and return (cleaned_text, violations).
        
        The cleaned text has dangerous content removed.
        Violations list describes what was found and removed.
        """
        if not isinstance(text, str):
            return str(text)[:self.MAX_INPUT_LENGTH], ["non_string_input_coerced"]
        
        violations = []
        cleaned = text
        
        # 1. Length check
        if len(cleaned) > self.MAX_INPUT_LENGTH:
            cleaned = cleaned[:self.MAX_INPUT_LENGTH]
            violations.append(f"truncated_from_{len(text)}_to_{self.MAX_INPUT_LENGTH}")
        
        # 2. Code injection
        for pattern in self._compiled_dangerous:
            if pattern.search(cleaned):
                violations.append(f"code_injection:{pattern.pattern[:30]}")
                cleaned = pattern.sub("[SANITIZED]", cleaned)
        
        # 3. Path traversal
        for pattern in self._compiled_path:
            if pattern.search(cleaned):
                violations.append(f"path_traversal:{pattern.pattern[:20]}")
                cleaned = pattern.sub("[PATH_BLOCKED]", cleaned)
        
        # 4. Prompt injection
        for pattern in self._compiled_injection:
            if pattern.search(cleaned):
                violations.append(f"prompt_injection:{pattern.pattern[:30]}")
                cleaned = pattern.sub("[INJECTION_BLOCKED]", cleaned)
        
        # Log violations
        if violations:
            self._violations.append({
                "context": context,
                "violations": violations,
                "timestamp": time.time(),
            })
            logger.warning(f"🛡️ Input sanitized ({context}): {violations}")
            
            # Publish event
            try:
                from unified_core.integration.event_bus import get_event_bus, EventPriority
                bus = get_event_bus()
                bus.publish_sync(
                    "security_violation",
                    {
                        "context": context,
                        "violations": violations,
                        "input_length": len(text),
                    },
                    "InputSanitizer",
                    EventPriority.CRITICAL
                )
            except Exception:
                pass
        
        return cleaned, violations
    
    def sanitize_proposition(self, proposition: str) -> str:
        """Sanitize a belief proposition specifically."""
        cleaned, violations = self.sanitize(proposition, "belief_proposition")
        return cleaned[:self.MAX_PROPOSITION_LENGTH]
    
    def get_violation_count(self) -> int:
        return len(self._violations)
    
    def get_recent_violations(self, limit: int = 10) -> List[Dict]:
        return self._violations[-limit:]


# ============================================================
#  2. Rate Limiter (Token Bucket)
# ============================================================

@dataclass
class TokenBucket:
    """Token bucket for rate limiting a specific resource."""
    capacity: float
    refill_rate: float  # tokens per second
    tokens: float = field(default=0.0)
    last_refill: float = field(default_factory=time.time)
    
    def __post_init__(self):
        self.tokens = self.capacity
    
    def consume(self, tokens: float = 1.0) -> bool:
        """Try to consume tokens. Returns True if allowed."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimiter:
    """
    Rate limiter for system resources.
    
    Prevents abuse of:
    - LLM calls (NeuralEngineClient)
    - Neuron creation (NeuronFabric)
    - Decision making (DecisionScorer)
    - Event publishing (EventBus)
    """
    
    DEFAULT_LIMITS = {
        "llm_call": (30, 2.0),      # 30 burst, 2/sec refill
        "neuron_create": (100, 5.0), # 100 burst, 5/sec refill
        "decision": (20, 1.0),       # 20 burst, 1/sec refill
        "event_publish": (200, 20.0),# 200 burst, 20/sec refill
        "belief_add": (50, 3.0),     # 50 burst, 3/sec refill
    }
    
    def __init__(self, custom_limits: Dict[str, Tuple[float, float]] = None):
        self._buckets: Dict[str, TokenBucket] = {}
        self._blocked_count: Dict[str, int] = defaultdict(int)
        
        limits = {**self.DEFAULT_LIMITS, **(custom_limits or {})}
        for resource, (capacity, rate) in limits.items():
            self._buckets[resource] = TokenBucket(capacity=capacity, refill_rate=rate)
    
    def allow(self, resource: str, tokens: float = 1.0) -> bool:
        """Check if action is allowed under rate limit."""
        bucket = self._buckets.get(resource)
        if not bucket:
            return True  # Unknown resource = no limit
        
        allowed = bucket.consume(tokens)
        if not allowed:
            self._blocked_count[resource] += 1
            logger.warning(f"⏱️ Rate limited: {resource} (blocked {self._blocked_count[resource]} times)")
        return allowed
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "buckets": {
                name: {
                    "tokens": round(b.tokens, 2),
                    "capacity": b.capacity,
                    "blocked": self._blocked_count.get(name, 0),
                }
                for name, b in self._buckets.items()
            }
        }


# ============================================================
#  3. Tamper Detector (NeuronFabric Integrity)
# ============================================================

class TamperDetector:
    """
    Detect unauthorized modifications to NeuronFabric persistence files.
    
    Mechanism:
    - On save: compute SHA-256 of serialized data → store as checksum
    - On load: recompute SHA-256 → compare with stored checksum
    - Mismatch = potential tampering → alert + mark as compromised
    
    HONESTY NOTE:
    An attacker who can modify the data file can also modify the checksum.
    This protects against accidental corruption and casual modification,
    NOT against a sophisticated attacker with full filesystem access.
    """
    
    CHECKSUM_SUFFIX = ".sha256"
    
    def __init__(self):
        self._alerts: List[Dict[str, Any]] = []
        self._verified_files: Set[str] = set()
    
    def compute_checksum(self, data: dict) -> str:
        """Compute deterministic SHA-256 checksum of data."""
        # Sort keys for deterministic output
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()
    
    def save_checksum(self, filepath: str, data: dict):
        """Save checksum alongside the data file."""
        checksum = self.compute_checksum(data)
        checksum_path = filepath + self.CHECKSUM_SUFFIX
        try:
            with open(checksum_path, "w") as f:
                json.dump({
                    "sha256": checksum,
                    "file": os.path.basename(filepath),
                    "timestamp": time.time(),
                    "neuron_count": len(data.get("neurons", {})),
                    "synapse_count": len(data.get("synapses", {})),
                }, f, indent=2)
            logger.debug(f"🔐 Checksum saved: {checksum[:16]}... → {checksum_path}")
        except Exception as e:
            logger.error(f"Failed to save checksum: {e}")
    
    def verify_integrity(self, filepath: str, data: dict) -> Dict[str, Any]:
        """
        Verify data integrity against stored checksum.
        
        Returns:
            {
                "verified": bool,
                "status": "ok" | "tampered" | "no_checksum" | "error",
                "details": str
            }
        """
        checksum_path = filepath + self.CHECKSUM_SUFFIX
        
        if not os.path.exists(checksum_path):
            return {
                "verified": False,
                "status": "no_checksum",
                "details": "No checksum file found — first run or checksum deleted"
            }
        
        try:
            with open(checksum_path, "r") as f:
                stored = json.load(f)
            
            expected = stored.get("sha256", "")
            actual = self.compute_checksum(data)
            
            if actual == expected:
                self._verified_files.add(filepath)
                return {
                    "verified": True,
                    "status": "ok",
                    "details": f"Integrity verified: {actual[:16]}..."
                }
            else:
                # TAMPERING DETECTED
                alert = {
                    "filepath": filepath,
                    "expected": expected[:16],
                    "actual": actual[:16],
                    "timestamp": time.time(),
                    "stored_neurons": stored.get("neuron_count", "?"),
                    "actual_neurons": len(data.get("neurons", {})),
                }
                self._alerts.append(alert)
                
                logger.critical(
                    f"🚨 TAMPER DETECTED: {filepath} — "
                    f"expected {expected[:16]}..., got {actual[:16]}..."
                )
                
                # Publish alert via EventBus
                try:
                    from unified_core.integration.event_bus import get_event_bus, EventPriority
                    bus = get_event_bus()
                    bus.publish_sync(
                        "tamper_detected",
                        alert,
                        "TamperDetector",
                        EventPriority.CRITICAL
                    )
                except Exception:
                    pass
                
                return {
                    "verified": False,
                    "status": "tampered",
                    "details": f"INTEGRITY VIOLATION: checksum mismatch"
                }
        
        except Exception as e:
            return {
                "verified": False,
                "status": "error",
                "details": f"Verification error: {e}"
            }
    
    def get_alerts(self) -> List[Dict]:
        return list(self._alerts)
    
    def is_compromised(self) -> bool:
        return len(self._alerts) > 0


# ============================================================
#  4. Command Validator (brain_tools.py security)
# ============================================================

class CommandValidator:
    """
    Validates shell commands and Python code before execution.
    Used by brain_tools.py to block dangerous operations.
    """
    
    DANGEROUS_SHELL_PATTERNS = [
        r'rm\s+-rf\s+/',                   # Recursive forced delete from root
        r'sudo\s+rm',                      # Sudo delete
        r'dd\s+if=',                       # Raw disk write
        r'mkfs\.',                         # Format filesystem
        r'>\s*/dev/sd',                    # Overwrite disk device
        r'chmod\s+777',                    # Dangerous permissions
        r'chown\s+root',                   # Change owner to root
        r'/etc/passwd',                    # Sensitive system file
        r'/etc/shadow',                    # Password file
        r'killall',                        # Kill all processes
        r'\bshutdown\b',                   # System shutdown
        r'\breboot\b',                     # System reboot
        r':\(\)\{.*\|.*&\}\s*;',           # Fork bomb
        r'wget\s+.*\|\s*sh',              # Download and execute
        r'curl\s+.*\|\s*(sh|bash)',        # Download and execute
    ]
    
    SAFE_SHELL_PREFIXES = [
        r'^ls\b',                          # List files
        r'^df\b',                          # Disk usage
        r'^free\b',                        # Memory
        r'^ps\b',                          # Processes
        r'^uname\b',                       # System info
        r'^cat\b',                         # Read file
        r'^head\b',                        # Read head
        r'^tail\b',                        # Read tail
        r'^wc\b',                          # Word count
        r'^grep\b',                        # Search text
        r'^find\b',                        # Find files
        r'^which\b',                       # Find binary
        r'^echo\b',                        # Echo
        r'^date\b',                        # Date
        r'^whoami\b',                      # Current user
        r'^pwd\b',                         # Current dir
        r'^id\b',                          # User ID
        r'^uptime\b',                      # System uptime
        r'^pip\s+(list|show|freeze)\b',    # Pip read-only
        r'^pip3\s+(list|show|freeze)\b',   # Pip3 read-only
        r'^git\s+(log|status|diff|show|branch)\b',  # Git read-only
        r'^python3?\s+',                   # Python (validated separately)
        r'^systemctl\s+status\b',          # Service status
        r'^journalctl\b',                  # System logs
        r'^du\b',                          # Dir usage
        r'^stat\b',                        # File stats
        r'^file\b',                        # File type
        r'^md5sum\b',                      # Checksum
        r'^sha256sum\b',                   # Checksum
        r'^netstat\b',                     # Network (read)
        r'^ss\b',                          # Socket stats
        r'^top\s+-bn1\b',                  # Top snapshot
        r'^nvidia-smi\b',                  # GPU info
        r'^lsblk\b',                       # Block devices
    ]
    
    DANGEROUS_PYTHON_PATTERNS = [
        r'__import__\s*\(',
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\bcompile\s*\(',
        r'\bos\.system\s*\(',
        r'\bos\.popen\s*\(',
        r'\bos\.exec',
        r'\bsubprocess\.',
        r'\bsocket\.',
        r'\bshutil\.rmtree\s*\(',
        r'\burllib\.request',
        r'\brequests\.(get|post|put|delete)\s*\(',
    ]
    
    WRITE_ALLOWED_PREFIXES = [
        "/home/noogh/projects/",
        "/home/noogh/.noogh/",
        "/tmp/",
        "/var/tmp/noogh",
    ]
    
    WRITE_BLOCKED_PREFIXES = [
        "/etc/",
        "/usr/",
        "/boot/",
        "/dev/",
        "/proc/",
        "/sys/",
        "/root/",
        "/var/log/",
    ]
    
    PROTECTED_PIDS = {1}  # init
    
    def __init__(self):
        self._compiled_dangerous = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_SHELL_PATTERNS]
        self._compiled_safe = [re.compile(p, re.IGNORECASE) for p in self.SAFE_SHELL_PREFIXES]
        self._compiled_python = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PYTHON_PATTERNS]
        self._block_count = 0
    
    def validate_shell_cmd(self, cmd: str) -> tuple:
        """
        Validate a shell command.
        Returns: (allowed: bool, reason: str)
        """
        cmd_stripped = cmd.strip()
        
        # 1. Check dangerous patterns (blacklist)
        for pattern in self._compiled_dangerous:
            if pattern.search(cmd_stripped):
                self._block_count += 1
                reason = f"Dangerous pattern blocked: {pattern.pattern[:30]}"
                logger.warning(f"🚨 Shell command BLOCKED: {reason} | cmd={cmd_stripped[:80]}")
                return False, reason
        
        # 2. Check safe prefixes (whitelist)
        for pattern in self._compiled_safe:
            if pattern.match(cmd_stripped):
                return True, "safe_prefix"
        
        # 3. Allow cd, mkdir, touch, cp, mv within project
        #    Allow pip install, python run (validated separately)
        project_safe = [
            r'^cd\s+/home/noogh/',
            r'^mkdir\s',
            r'^touch\s',
            r'^cp\s',
            r'^mv\s',
            r'^pip3?\s+install\b',
            r'^timeout\s',
        ]
        for p in project_safe:
            if re.match(p, cmd_stripped, re.IGNORECASE):
                return True, "project_safe"
        
        # 4. Unknown command → block (conservative)
        self._block_count += 1
        return False, f"Command not in safe list. Use force=True to override."
    
    def validate_python_code(self, code: str) -> tuple:
        """
        Validate Python code before execution.
        Returns: (allowed: bool, reason: str)
        """
        for pattern in self._compiled_python:
            if pattern.search(code):
                self._block_count += 1
                reason = f"Dangerous Python pattern: {pattern.pattern[:30]}"
                logger.warning(f"🚨 Python code BLOCKED: {reason}")
                return False, reason
        return True, "ok"
    
    def validate_write_path(self, path: str) -> tuple:
        """
        Validate a file write path.
        Returns: (allowed: bool, reason: str)
        """
        resolved = os.path.realpath(path)
        
        # Block dangerous paths first
        for prefix in self.WRITE_BLOCKED_PREFIXES:
            if resolved.startswith(prefix):
                return False, f"Write blocked: {prefix}* is protected"
        
        # Allow known safe paths
        for prefix in self.WRITE_ALLOWED_PREFIXES:
            if resolved.startswith(prefix):
                return True, "allowed_path"
        
        return False, f"Write blocked: path outside allowed directories"
    
    def validate_pid(self, pid: int) -> tuple:
        """
        Validate a PID before killing.
        Returns: (allowed: bool, reason: str)
        """
        if pid in self.PROTECTED_PIDS:
            return False, f"PID {pid} is protected (init)"
        if pid <= 0:
            return False, f"Invalid PID: {pid}"
        return True, "ok"
    
    @property
    def blocked_count(self) -> int:
        return self._block_count


# ============================================================
#  Singletons
# ============================================================

_sanitizer: Optional[InputSanitizer] = None
_rate_limiter: Optional[RateLimiter] = None
_tamper_detector: Optional[TamperDetector] = None
_command_validator: Optional[CommandValidator] = None

def get_sanitizer() -> InputSanitizer:
    global _sanitizer
    if _sanitizer is None:
        _sanitizer = InputSanitizer()
    return _sanitizer

def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

def get_tamper_detector() -> TamperDetector:
    global _tamper_detector
    if _tamper_detector is None:
        _tamper_detector = TamperDetector()
    return _tamper_detector

def get_command_validator() -> CommandValidator:
    global _command_validator
    if _command_validator is None:
        _command_validator = CommandValidator()
    return _command_validator

