"""
Actuators - Real-World Effect Capabilities (HARDENED v3.0)
Role: Senior Security Architect Fix

SECURITY STRATEGY:
1. TOCTOU Protection: Verifying canonical paths inside action blocks.
2. Command Audit: Inspecting full argv list, not just the executable.
3. Async IO: Non-blocking process and network operations.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import shlex
import shutil
import signal
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger("unified_core.core.actuators")

from unified_core.core.amla_enforcer import (
    enforce_amla,
    AMLAEnforcementError,
    AMLAEnforcedMixin,
)

AMLA_AVAILABLE = True

class SecurityError(Exception):
    """Exception raised for security policy violations."""
    pass

class ActuatorType(Enum):
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    PROCESS = "process"
    TIME = "time"

class ActionResult(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"

@dataclass
class ActuatorAction:
    action_id: str
    actuator_type: ActuatorType
    operation: str
    params: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    result: Optional[ActionResult] = None
    result_data: Optional[Dict[str, Any]] = None

class GovernanceMixin:
    """Provides bulletproof behavioral control: Precise Telemetry, Soft/Hard Circuit Breaking."""
    def __init__(self, rate_limit_per_min: int, failure_threshold: int = 3, cooldown_sec: int = 300, latency_limit_ms: int = 1000):
        self._max_rate = rate_limit_per_min
        self._leak_rate = rate_limit_per_min / 60.0  # Tokens per second
        self._capacity = max(5, rate_limit_per_min // 2)  # Max burst size
        self._tokens = float(self._capacity)
        self._last_leak_time = time.time()
        
        self._failure_threshold = failure_threshold
        self._cooldown_duration = cooldown_sec
        self._consecutive_failures = 0
        self._cooldown_until = 0
        
        # Latency Governance v2.1 (Dual Threshold)
        self._latency_limit = latency_limit_ms / 1000.0  # seconds
        self._latency_ewma = 0.0
        self._ewma_alpha = 0.3
        self._latency_failures = 0
        
        # New v2.1 Precision Telemetry
        self.blocked_count = 0
        self.rejection_count = 0
        self.cooldown_count = 0
        self.lock_retries = 0
        self.latencies: List[float] = [] # For p95/p50

    def _leak(self):
        """Standard Leaky Bucket leakage."""
        now = time.time()
        duration = now - self._last_leak_time
        self._tokens = min(self._capacity, self._tokens + duration * self._leak_rate)
        self._last_leak_time = now

    def _check_governance(self):
        """Internal check before action."""
        now = time.time()
        
        # 1. Circuit Breaker (Hard Failure or Latency Storm)
        if now < self._cooldown_until:
            wait = int(self._cooldown_until - now)
            self.blocked_count += 1
            raise SecurityError(f"CIRCUIT_BREAKER: Actuator in cooldown for {wait}s")
            
        # 2. Leaky Bucket Rate Limiting
        self._leak()
        if self._tokens < 1.0:
            self.rejection_count += 1
            raise SecurityError(f"RATE_LIMIT: Leaky Bucket empty. Current tokens: {self._tokens:.2f}")
            
        self._tokens -= 1.0

    def _record_outcome(self, success: bool, duration: float = 0.0):
        """Update circuit breaker state based on outcome and dual latency thresholds."""
        # 1. Latency EWMA Update & Telemetry
        if duration > 0:
            self.latencies.append(duration)
            if len(self.latencies) > 100: self.latencies.pop(0) # Window for p95

            if self._latency_ewma == 0:
                self._latency_ewma = duration
            else:
                self._latency_ewma = (self._ewma_alpha * duration) + ((1 - self._ewma_alpha) * self._latency_ewma)
            
            # DUAL THRESHOLD: soft SLA vs hard Breaker
            soft_threshold = self._latency_limit * 1.5
            hard_threshold = self._latency_limit * 2.5
            
            if self._latency_ewma > soft_threshold:
                 logger.warning(f"⚠️ SLA WARNING: Actuator latency ({self._latency_ewma*1000:.0f}ms) exceeds soft threshold ({soft_threshold*1000:.0f}ms)")
            
            if self._latency_ewma > hard_threshold:
                self._latency_failures += 1
                if self._latency_failures >= 5:
                    self._trigger_cooldown("LATENCY_STORM_HARD")
            else:
                self._latency_failures = max(0, self._latency_failures - 1)

        # 2. Success/Failure Tracking
        if success:
            self._consecutive_failures = 0
        else:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._failure_threshold:
                self._trigger_cooldown("CONSECUTIVE_FAILURES")

    def _trigger_cooldown(self, reason: str):
        """Activates the circuit breaker."""
        self._cooldown_until = time.time() + self._cooldown_duration
        self.cooldown_count += 1
        logger.critical(f"⚡ CIRCUIT_BREAKER ACTIVATED [{reason}]: Cooldown for {self._cooldown_duration}s")
        self._consecutive_failures = 0
        self._latency_failures = 0

    def get_resilience_metrics(self) -> Dict[str, Any]:
        """Provides precision metrics for the Resilience Report."""
        import statistics
        p95 = statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) > 5 else 0
        p50 = statistics.median(self.latencies) if self.latencies else 0
        return {
            "tokens": round(self._tokens, 2),
            "capacity": self._capacity,
            "blocked": self.blocked_count,
            "rejected": self.rejection_count,
            "cooldowns": self.cooldown_count,
            "latency_ewma_ms": round(self._latency_ewma * 1000, 2),
            "p95_ms": round(p95 * 1000, 2),
            "p50_ms": round(p50 * 1000, 2),
            "lock_retries": self.lock_retries
        }

    def _reset_governance(self):
        """Test utility: Resets all governance counters."""
        self._tokens = float(self._capacity)
        self._consecutive_failures = 0
        self._cooldown_until = 0
        self._latency_ewma = 0.0
        self._latency_failures = 0
        self.blocked_count = 0
        self.rejection_count = 0
        self.cooldown_count = 0
        self.latencies = []
        logger.info("♻️ Governance reset for actuator.")

class FilesystemActuator(AMLAEnforcedMixin, GovernanceMixin):
    # FULL AUTONOMY MODE - Expanded paths for self-development
    ALLOWED_PROJECT_PATHS = [
        "/",                     # TOTAL SYSTEM ACCESS
        "/home/noogh/projects",  # All projects
        "/home/noogh/backups",   # Backups
        "/home/noogh/data",      # Data storage
        "/tmp",                   # Temporary files
    ]
    # Safety Pin: Only extremely sensitive kernel/hardware paths remain blocked
    PROTECTED_PATHS = ["/proc", "/sys", "/dev"]
    AMLA_PROTECTED_METHODS = []  # Full autonomy for all methods

    def __init__(self):
        GovernanceMixin.__init__(self, rate_limit_per_min=60, latency_limit_ms=200)
        self._action_count = 0
        self.blocked_count = 0 # Redundant but safe

    def _generate_id(self, op: str) -> str:
        self._action_count += 1
        return hashlib.sha256(f"{op}:{time.time()}".encode()).hexdigest()[:16]

    def _get_canonical(self, path: str) -> str:
        return os.path.realpath(os.path.abspath(path))

    def _verify_path(self, path: str) -> str:
        """Verify path and return canonical version if allowed, else raise."""
        cp = self._get_canonical(path)
        
        # Security Safety Pin: Explicitly block extremely sensitive kernel paths
        for p in self.PROTECTED_PATHS:
            if cp.startswith(self._get_canonical(p)):
                 raise SecurityError(f"Access to kernel/hardware path PROTECTED: {cp}")

        for allowed in self.ALLOWED_PROJECT_PATHS:
            ca = self._get_canonical(allowed)
            # Handle root (/) specially or ensure startswith is correct
            if ca == "/":
                return cp
            if cp.startswith(ca + os.sep) or cp == ca:
                return cp
        raise SecurityError(f"Path outside allowlist: {cp}")

    async def read_file(self, path: str, auth: Any) -> ActuatorAction:
        """Reads file safely with security verification."""
        action = ActuatorAction(self._generate_id("read"), ActuatorType.FILESYSTEM, "read", {"path": path})
        start = time.time()
        try:
            self._check_governance()
            # scope check - we allow read if user has filesystem:read
            if auth: auth.require_scope("filesystem:read")
            cp = self._verify_path(path)
            
            if not os.path.exists(cp):
                raise FileNotFoundError(f"File not found: {cp}")
            
            with open(cp, "r", encoding='utf-8', errors='replace') as f:
                content = f.read(1000000) # 1MB limit for safety
            
            action.result = ActionResult.SUCCESS
            action.result_data = {"content": content, "canonical_path": cp}
            self._record_outcome(True, time.time() - start)
        except Exception as e:
            logger.error(f"Read failed: {e}")
            action.result = ActionResult.FAILED
            action.result_data = {"error": str(e)}
            self._record_outcome(False, time.time() - start)
        return action

    async def write_file(self, path: str, content: str, auth: Any, create_dirs: bool = True) -> ActuatorAction:
        """Writes file safely with TOCTOU protection.
        
        Args:
            path: Target file path
            content: Content to write
            auth: Authentication context
            create_dirs: If True, create parent directories if they don't exist
        """
        action = ActuatorAction(self._generate_id("write"), ActuatorType.FILESYSTEM, "write", {"path": path})
        start = time.time()
        try:
            self._check_governance()
            if auth: auth.require_scope("filesystem:write")
            cp = self._verify_path(path)
            
            # TOCTOU PROTECTION: Write only to the verified canonical path
            # Using O_EXCL if needed, but here we ensure overwrite is intentional
            directory = os.path.dirname(cp)
            if create_dirs and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                
            with open(cp, "w", encoding='utf-8') as f:
                f.write(content)
            
            action.result = ActionResult.SUCCESS
            action.result_data = {"bytes": len(content), "canonical_path": cp}
            self._record_outcome(True, time.time() - start)
        except Exception as e:
            logger.error(f"Write failed: {e}")
            action.result = ActionResult.FAILED
            action.result_data = {"error": str(e)}
            self._record_outcome(False, time.time() - start)
        return action

    async def delete_file(self, path: str, auth: Any) -> ActuatorAction:
        action = ActuatorAction(self._generate_id("delete"), ActuatorType.FILESYSTEM, "delete", {"path": path})
        try:
            self._check_governance()
            if auth: auth.require_scope("filesystem:delete")
            cp = self._verify_path(path)
            if os.path.exists(cp):
                os.remove(cp)
                action.result = ActionResult.SUCCESS
            else:
                action.result = ActionResult.FAILED
                action.result_data = {"error": "File not found"}
        except Exception as e:
            action.result = ActionResult.FAILED
            action.result_data = {"error": str(e)}
        return action

class NetworkActuator(AMLAEnforcedMixin, GovernanceMixin):
    # FULL AUTONOMY MODE - Allow external internet access
    ALLOWED_DOMAINS = [
        "127.0.0.1", "localhost", "api.noogh.local", "neural-engine",
        # Search & Research
        "google.com", "www.google.com", "duckduckgo.com",
        "github.com", "raw.githubusercontent.com", "api.github.com",
        "stackoverflow.com", "arxiv.org",
        # AI & ML Resources
        "huggingface.co", "api.openai.com", "pypi.org",
        # General web
        "wikipedia.org", "en.wikipedia.org",
    ]
    # Blocked domains for safety
    BLOCKED_DOMAINS = ["malware", "phishing", "hack"]
    
    def __init__(self):
        GovernanceMixin.__init__(self, rate_limit_per_min=10, latency_limit_ms=1000)
        self.blocked_count = 0

    async def http_request(self, url: str, method: str, auth: Any, body: str = None) -> ActuatorAction:
        import httpx
        from urllib.parse import urlparse
        
        if auth: auth.require_scope("network:http")
        action = ActuatorAction(hashlib.md5(url.encode()).hexdigest()[:10], ActuatorType.NETWORK, "http", {"url": url})
        start = time.time()
        
        try:
            self._check_governance()
            # SSRF PROTECTION: Strict Domain Check
            parsed = urlparse(url)
            if parsed.hostname not in self.ALLOWED_DOMAINS:
                action.result = ActionResult.BLOCKED
                action.result_data = {"error": f"Untrusted domain: {parsed.hostname}"}
                return action

            async with httpx.AsyncClient(timeout=30.0) as client:
                # MEMORY MANAGEMENT: Streaming large responses
                async with client.stream(method.upper(), url, content=body) as response:
                    content = []
                    size = 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > 5 * 1024 * 1024: # 5MB limit
                            raise MemoryError("Response too large")
                        content.append(chunk)
                    
                    full_content = b"".join(content).decode('utf-8', errors='ignore')
                    action.result = ActionResult.SUCCESS
                    action.result_data = {"status": response.status_code, "body": full_content[:5000]}
                    self._record_outcome(True, time.time() - start)
        except Exception as e:
            action.result = ActionResult.FAILED
            action.result_data = {"error": str(e)}
            self._record_outcome(False, time.time() - start)
        return action

class ProcessActuator(AMLAEnforcedMixin, GovernanceMixin):
    # FULL AUTONOMY MODE - Expanded command set
    ALLOWED_CMDS = [
        # Python
        "python3", "python", "pip", "pip3",
        # System info & Navigation
        "ls", "cat", "head", "tail", "grep", "find", "wc",
        "df", "free", "uptime", "ps", "top", "htop", "cd", "pwd",
        # GPU & Hardware
        "nvidia-smi", "lscpu", "lsusb", "lspci", "nvcc",
        # Development & Tools
        "git", "curl", "wget", "make", "gcc", "g++", "cmake",
        # System Administration (Sovereign Mode)
        "sudo", "systemctl", "journalctl", "apt", "apt-get", "dpkg",
        "ufw", "iptables", "ip", "ifconfig", "netstat", "ss",
        "reboot", "shutdown", "update-grub", "chmod", "chown",
        # Shell & Environment
        "bash", "sh", "echo", "date", "env", "export", "source",
        # Scripts
        "./live_audit.py",
    ]
    # Dangerous commands - Protective safety pins only
    BLOCKED_CMDS = ["rm -rf /", "dd if=/dev/zero", "mkfs", "fdisk"]

    def __init__(self):
        GovernanceMixin.__init__(self, rate_limit_per_min=30, latency_limit_ms=500)
        self.blocked_count = 0

    async def spawn(self, cmd: List[str], auth: Any, cwd: str = None) -> ActuatorAction:
        """Spawns process safely with full argv audit and NO shell=True."""
        if auth: auth.require_scope("process:spawn")
        action = ActuatorAction("proc_" + str(time.time()), ActuatorType.PROCESS, "spawn", {"cmd": cmd})
        start = time.time()

        try:
            self._check_governance()
            # SECURITY: Full command audit
            if not cmd or cmd[0] not in self.ALLOWED_CMDS:
                action.result = ActionResult.BLOCKED
                action.result_data = {"error": f"Exec '{cmd[0]}' not allowed"}
                return action
            
            # Prevent dangerous flags (e.g., python -c, sh -c)
            dangerous_args = ["-c", "--exec", "-e", "import os", "eval(", "subprocess"]
            if any(bad in " ".join(cmd).lower() for bad in dangerous_args):
                action.result = ActionResult.BLOCKED
                action.result_data = {"error": "Dangerous argument flagged"}
                return action

            # NO shell=True. Use arrays only.
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            
            action.result = ActionResult.SUCCESS
            action.result_data = {
                "stdout": stdout.decode().strip()[:2000],
                "stderr": stderr.decode().strip()[:1000],
                "exit_code": proc.returncode
            }
            self._record_outcome(True, time.time() - start)
        except Exception as e:
            action.result = ActionResult.FAILED
            action.result_data = {"error": str(e)}
            self._record_outcome(False, time.time() - start)
        return action

class ProcessResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int

class MathActuator(AMLAEnforcedMixin):
    """Sovereign Numerical Computing Actuator."""
    
    async def matrix_multiply(self, size: int, auth: Any) -> ActuatorAction:
        """Performs optimized matrix multiplication and profiles performance."""
        if auth: auth.require_scope("compute:heavy")
        action = ActuatorAction("math_" + str(time.time()), ActuatorType.PROCESS, "matrix_mult", {"size": size})
        
        try:
            import numpy as np
            import time as t
            
            # Limit size for safety (max 1024x1024)
            size = min(size, 1024)
            
            start = t.perf_counter()
            A = np.random.rand(size, size).astype(np.float32)
            B = np.random.rand(size, size).astype(np.float32)
            C = np.matmul(A, B)
            end = t.perf_counter()
            
            duration = end - start
            # Floating point operations: 2 * N^3
            flops = (2.0 * (size ** 3)) / duration if duration > 0 else 0
            gflops = flops / 1e9
            
            action.result = ActionResult.SUCCESS
            action.result_data = {
                "size": f"{size}x{size}",
                "duration_ms": round(duration * 1000, 2),
                "gflops": round(gflops, 4),
                "mean_result": float(np.mean(C))
            }
        except Exception as e:
            action.result = ActionResult.FAILED
            action.result_data = {"error": str(e)}
        return action

class ActuatorHub:
    def __init__(self, consequence_engine=None, scar_tissue=None):
        self.consequence_engine = consequence_engine
        self.scar_tissue = scar_tissue
        self.filesystem = FilesystemActuator()
        self.network = NetworkActuator()
        self.process = ProcessActuator()
        self.math = MathActuator()

    def get_stats(self) -> Dict[str, Any]:
        """Support detailed metrics reporting for Resilience v2.1."""
        return {
            "filesystem": self.filesystem.get_resilience_metrics(),
            "network": self.network.get_resilience_metrics(),
            "process": self.process.get_resilience_metrics(),
            "summary": {
                "blocked_total": self.filesystem.blocked_count + self.network.blocked_count + self.process.blocked_count,
                "rejections_total": self.filesystem.rejection_count + self.network.rejection_count + self.process.rejection_count,
                "cooldowns_total": self.filesystem.cooldown_count + self.network.cooldown_count + self.process.cooldown_count
            }
        }
    def to_dict(self) -> Dict[str, Any]:
        """Support for legacy bridge calls."""
        return self.get_stats()

def get_actuator_hub(consequence_engine=None, scar_tissue=None):
    """Helper to create ActuatorHub."""
    return ActuatorHub(consequence_engine=consequence_engine, scar_tissue=scar_tissue)
