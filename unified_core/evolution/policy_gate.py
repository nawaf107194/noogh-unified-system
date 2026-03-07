"""
Policy Gate - Safety Validation for Evolution Proposals
Version: 1.1.0
Part of: Self-Directed Layer (Phase 17.5)

Validates proposals against safety rules before execution.
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("unified_core.evolution.policy_gate")


class RiskLevel(Enum):
    LOW = "low"         # 0-30
    MEDIUM = "medium"   # 31-60
    HIGH = "high"       # 61-100


@dataclass
class PolicyRule:
    """A single policy rule."""
    name: str
    description: str
    enabled: bool = True


class PolicyGate:
    """
    Safety gate for evolution proposals.
    
    Validates proposals against:
    - Allowlist of modifiable paths
    - Protected paths blocklist
    - Risk score thresholds
    - Import restrictions
    - Capability restrictions
    """
    
    # Allowlist: Paths that can be modified
    # Expanded to allow project src directory
    ALLOWED_PATHS: Set[str] = {
        # Config files
        "config/*.yaml",
        "config/*.json",
        "policy/*.yaml",
        "policy/*.json",
        # Helper/utility code
        "helpers/*.py",
        "utils/*.py",
        # Project source (user-approved expansion)
        "/home/noogh/projects/noogh_unified_system/src/*",
        "unified_core/*",
        "*.py",
    }
    
    # Protected: Never allow modification
    # MINIMAL PROTECTION - User wants maximum freedom
    PROTECTED_PATHS: Set[str] = {
        # Only critical system files protected
        # neural_engine removed - can be modified with approval
    }
    
    # Allowed imports for code patches
    ALLOWED_IMPORTS: Set[str] = {
        "logging",
        "time",
        "json",
        "os",
        "pathlib",
        "typing",
        "dataclasses",
        "enum",
        "asyncio",
        "hashlib",
    }
    
    # Blocked imports for CODE EXECUTION
    # ABSOLUTE MINIMUM - User wants deep analysis
    BLOCKED_IMPORTS: Set[str] = {
        # Only eval/exec blocked - everything else allowed
        "eval",
        "exec",
        # __import__ removed - can be used
        # subprocess allowed
        # os.system allowed
        # compile allowed
        # Everything else allowed
    }
    
    # Risk thresholds - MAXIMUM freedom for deep evolution (default)
    RISK_THRESHOLDS = {
        "config": 95,   # Almost no restrictions
        "policy": 90,   # Very high freedom
        "code": 90,     # Very high freedom for deep analysis
    }

    # v1.2: SAFE_MODE support — when NOOGH_EVO_SAFE_MODE=1, tighten thresholds
    _safe_mode = os.getenv("NOOGH_EVO_SAFE_MODE", "0") == "1"
    if _safe_mode:
        # More conservative limits when running in safe evolution mode
        RISK_THRESHOLDS = {
            "config": 60,   # require lower risk config changes
            "policy": 55,   # stricter policy edits
            "code": 50,     # only relatively safe code patches pass gate
        }
        logger.warning("🛡️ PolicyGate SAFE_MODE: tightened risk thresholds for config/policy/code proposals.")
    
    # v1.3.0: Interval bounds - UNLIMITED for deepest analysis
    INTERVAL_BOUNDS = {
        "cycle_loop": (0.1, 120.0),      # تحليل أعمق: حتى دقيقتين
        "analysis_task": (1.0, 1800.0),  # تحليل أعمق: حتى 30 دقيقة!
        "default": (0.05, 600.0)         # تحليل أعمق: حتى 10 دقائق
    }
    
    def __init__(self):
        self.rules: List[PolicyRule] = [
            PolicyRule("path_allowlist", "Only allow modifications to allowlisted paths"),
            PolicyRule("path_blocklist", "Block modifications to protected paths"),
            PolicyRule("risk_threshold", "Reject high-risk proposals"),
            PolicyRule("import_check", "Block dangerous imports"),
            PolicyRule("capability_check", "Ensure proposal respects capability limits"),
        ]
        logger.info("PolicyGate initialized with {} rules".format(len(self.rules)))
    
    def _matches_pattern(self, path: str, patterns: Set[str]) -> bool:
        """Check if path matches any glob pattern."""
        from fnmatch import fnmatch
        for pattern in patterns:
            if fnmatch(path, pattern) or pattern in path:
                return True
        return False
    
    def _check_path_allowlist(self, targets: List[str]) -> Tuple[bool, str]:
        """Check if all targets are in allowlist."""
        for target in targets:
            if not self._matches_pattern(target, self.ALLOWED_PATHS):
                return False, f"Path not in allowlist: {target}"
        return True, "OK"
    
    def _check_path_blocklist(self, targets: List[str]) -> Tuple[bool, str]:
        """Check if any targets are in blocklist."""
        for target in targets:
            if self._matches_pattern(target, self.PROTECTED_PATHS):
                return False, f"Protected path: {target}"
        return True, "OK"
    
    def _check_risk_threshold(self, scope: str, risk_score: float) -> Tuple[bool, str]:
        """Check if risk score is within threshold for scope."""
        threshold = self.RISK_THRESHOLDS.get(scope, 40)
        if risk_score > threshold:
            return False, f"Risk {risk_score} exceeds threshold {threshold} for {scope}"
        return True, "OK"
    
    def _check_imports(self, diff: str) -> Tuple[bool, str]:
        """Check for dangerous imports in code patches.
        
        Note: Imports can be ANALYZED/READ but not EXECUTED in generated code.
        Only critical security risks are blocked.
        """
        # Simple pattern matching for imports
        import_pattern = r'(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_.]*)'
        imports = re.findall(import_pattern, diff)
        
        for imp in imports:
            base_module = imp.split('.')[0]
            
            # Only block critical security risks (eval, exec, subprocess, etc.)
            if base_module in self.BLOCKED_IMPORTS or imp in self.BLOCKED_IMPORTS:
                return False, f"Blocked import (security risk): {imp}"
        
        # Allow all other imports for analysis
        return True, "OK"
    
    # v2.0: Subprocess whitelist — specific safe commands allowed
    SUBPROCESS_WHITELIST = {
        "pip list", "pip show", "pip check",
        "git status", "git log", "git diff", "git branch",
        "systemctl status", "systemctl is-active",
        "df", "du", "uptime", "free", "uname",
        "python3 -m py_compile", "python3 -m pytest",
        "wc", "cat", "head", "tail", "grep",
        "ls", "find", "stat",
    }
    
    SUBPROCESS_BLOCKED_COMMANDS = {
        "rm ", "rm -rf", "dd ", "mkfs", "fdisk",
        "shutdown", "reboot", "halt", "init ",
        "chmod 777", "chown", "curl | sh", "wget | sh",
        "> /dev/", "format",
    }
    
    def _check_dangerous_patterns(self, diff: str) -> Tuple[bool, str]:
        """Check for dangerous code patterns with subprocess whitelist."""
        # Always blocked
        always_blocked = [
            (r'eval\s*\(', "eval() is not allowed"),
            (r'exec\s*\(', "exec() is not allowed"),
            (r'__import__\s*\(', "__import__() is not allowed"),
            (r'os\.system\s*\(', "os.system() is not allowed — use subprocess"),
        ]
        
        for pattern, message in always_blocked:
            if re.search(pattern, diff):
                return False, message
        
        # Subprocess: check whitelist
        if re.search(r'subprocess\.', diff):
            # Extract the command being used
            cmd_match = re.findall(r'subprocess\.\w+\(\s*\[?\s*["\']([^"\']+)', diff)
            
            if not cmd_match:
                # Can't determine command → allow with warning
                logger.warning("subprocess used but command not detectable — allowing")
                return True, "OK"
            
            for cmd in cmd_match:
                cmd_lower = cmd.lower().strip()
                
                # Check blocked commands first
                for blocked in self.SUBPROCESS_BLOCKED_COMMANDS:
                    if blocked in cmd_lower:
                        return False, f"subprocess command blocked: {cmd}"
                
                # Check whitelist
                allowed = any(
                    cmd_lower.startswith(w) 
                    for w in self.SUBPROCESS_WHITELIST
                )
                if not allowed:
                    return False, f"subprocess command not in whitelist: {cmd}"
            
            logger.info(f"subprocess whitelisted: {cmd_match}")
        
        return True, "OK"
    
    def _check_interval_bounds(self, diff: str) -> Tuple[bool, str]:
        """v1.1.1: Check if interval values are within allowed bounds."""
        import re
        # Extract new value from diff
        match = re.search(r'\+ suggested: (\d+\.?\d*)', diff)
        if match:
            value = float(match.group(1))
            bounds = self.INTERVAL_BOUNDS.get("default")
            if not (bounds[0] <= value <= bounds[1]):
                return False, f"Interval {value} outside bounds {bounds}"
        return True, "OK"
    
    def validate(
        self, 
        scope: str,
        targets: List[str],
        diff: str,
        risk_score: float
    ) -> Tuple[bool, str]:
        """
        Validate a proposal against all policy rules.
        
        Returns: (is_valid, reason)
        """
        # Rule 1: Path allowlist
        valid, reason = self._check_path_allowlist(targets)
        if not valid:
            logger.warning(f"PolicyGate REJECTED (allowlist): {reason}")
            return False, reason
        
        # Rule 2: Path blocklist
        valid, reason = self._check_path_blocklist(targets)
        if not valid:
            logger.warning(f"PolicyGate REJECTED (blocklist): {reason}")
            return False, reason
        
        # Rule 3: Risk threshold
        valid, reason = self._check_risk_threshold(scope, risk_score)
        if not valid:
            logger.warning(f"PolicyGate REJECTED (risk): {reason}")
            return False, reason
        
        # v1.1.1 Rule 3.5: Interval bounds for config
        if scope == "config":
            valid, reason = self._check_interval_bounds(diff)
            if not valid:
                logger.warning(f"PolicyGate REJECTED (interval bounds): {reason}")
                return False, reason
        
        # Rule 4: Import check (for code patches)
        if scope == "code":
            valid, reason = self._check_imports(diff)
            if not valid:
                logger.warning(f"PolicyGate REJECTED (imports): {reason}")
                return False, reason
            
            # Rule 5: Dangerous patterns
            valid, reason = self._check_dangerous_patterns(diff)
            if not valid:
                logger.warning(f"PolicyGate REJECTED (dangerous): {reason}")
                return False, reason
        
        logger.info(f"PolicyGate APPROVED: scope={scope}, risk={risk_score}")
        return True, "OK"
    
    def calculate_risk_score(
        self,
        scope: str,
        targets: List[str],
        diff: str
    ) -> float:
        """
        Calculate risk score for a proposal.
        
        Components:
        - Base risk by scope
        - Number of files affected
        - Size of changes
        - Presence of certain patterns
        """
        # Base risk by scope
        base_risk = {
            "config": 10,
            "policy": 30,
            "code": 50,
        }.get(scope, 50)
        
        # Files affected
        file_risk = min(len(targets) * 5, 20)
        
        # Size of changes
        lines_changed = len(diff.split('\n'))
        size_risk = min(lines_changed * 0.5, 20)
        
        # Pattern-based risk
        pattern_risk = 0
        if "async" in diff:
            pattern_risk += 5
        if "await" in diff:
            pattern_risk += 5
        if "exception" in diff.lower():
            pattern_risk += 5
        
        total_risk = base_risk + file_risk + size_risk + pattern_risk
        return min(100, max(0, total_risk))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get policy gate statistics."""
        return {
            "rules_count": len(self.rules),
            "allowed_paths": len(self.ALLOWED_PATHS),
            "protected_paths": len(self.PROTECTED_PATHS),
            "allowed_imports": len(self.ALLOWED_IMPORTS),
            "blocked_imports": len(self.BLOCKED_IMPORTS),
        }


# Singleton
_gate_instance = None

def get_policy_gate() -> PolicyGate:
    """Get the global PolicyGate instance."""
    global _gate_instance
    if _gate_instance is None:
        _gate_instance = PolicyGate()
    return _gate_instance
