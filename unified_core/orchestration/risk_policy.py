"""
NOOGH Risk Routing Policy

Defines risk classification and routing rules for tools and operations.

CRITICAL: This is the security policy that determines isolation boundaries.
"""

from enum import Enum
from typing import Dict, List
from unified_core.orchestration.messages import RiskLevel


class ToolRiskClassification:
    """
    Classification of tools by risk level.
    
    BASE RULE: Fail-closed. If uncertain → elevate to higher risk tier.
    """
    
    # SAFE: Read-only, no side effects, pure functions
    SAFE_TOOLS = {
        "fs.read",
        "fs.list",
        "fs.exists",
        "sys.info",
        "sys.processes",
        "sys.disk_usage",
        "mem.search",  # Read-only memory search
        "dev.repo_overview",
        "dev.search_code",
        "dev.git_status",
        "dev.git_diff",
        "dev.find_entrypoints",
        "util.noop",
        "util.finish",
        "ml.search_datasets",  # Search only
    }
    
    # RESTRICTED: Side effects but controlled (sandbox, allowlist, no network)
    RESTRICTED_TOOLS = {
        "code.exec_python",  # Sandbox required
        "dev.run_tests",  # Sandbox required
        "fs.write",  # Allowlist + canonicalization enforced
        "ml.load_dataset",  # Downloads but controlled
    }
    
    # DANGEROUS: System commands, network access, sensitive operations
    DANGEROUS_TOOLS = {
        "proc.run",  # Shell execution
        "net.http_get",  # Network access
        "net.http_post",  # Network + data exfiltration risk
        "fs.delete",  # Irreversible
        "mem.record",  # Modifies persisted state
        "ml.train_classifier",  # GPU intensive, file writes
    }
    
    @classmethod
    def classify_tool(cls, tool_name: str) -> RiskLevel:
        """
        Classify tool by risk level.
        
        Returns:
            RiskLevel enum
        """
        if tool_name in cls.SAFE_TOOLS:
            return RiskLevel.SAFE
        elif tool_name in cls.RESTRICTED_TOOLS:
            return RiskLevel.RESTRICTED
        elif tool_name in cls.DANGEROUS_TOOLS:
            return RiskLevel.DANGEROUS
        else:
            # FAIL-CLOSED: Unknown tools are DANGEROUS
            return RiskLevel.DANGEROUS
    
    @classmethod
    def classify_operation(
        cls,
        operation_desc: str,
        keywords: List[str]
    ) -> RiskLevel:
        """
        Classify operation by description and keywords.
        
        Used for natural language requests.
        """
        # Danger keywords
        DANGER_KEYWORDS = [
            "attack", "penetration", "exploit", "hack", "breach",
            "network", "download", "upload", "delete", "remove",
            "shell", "command", "exec", "run", "system"
        ]
        
        # Restricted keywords
        RESTRICTED_KEYWORDS = [
            "write", "create", "modify", "test", "build",
            "execute", "code", "python", "script"
        ]
        
        lower_desc = operation_desc.lower()
        lower_keywords = [k.lower() for k in keywords]
        
        # Check for danger
        if any(kw in lower_desc or kw in lower_keywords for kw in DANGER_KEYWORDS):
            return RiskLevel.DANGEROUS
        
        # Check for restricted
        if any(kw in lower_desc or kw in lower_keywords for kw in RESTRICTED_KEYWORDS):
            return RiskLevel.RESTRICTED
        
        # Default: SAFE
        return RiskLevel.SAFE


class ChainDetector:
    """
    Detects dangerous tool chaining patterns.
    
    Patterns blocked:
    - write → exec (malicious code injection)
    - read_secrets → network (data exfiltration)
    - download → exec (remote code execution)
    """
    
    BLOCKED_CHAINS = [
        # (first_tools, second_tools, description)
        (["fs.write"], ["code.exec_python", "proc.run"], "write_then_exec"),
        (["mem.search"], ["net.http_post", "net.http_get"], "memory_exfiltration"),
        (["net.http_get"], ["code.exec_python", "proc.run"], "download_and_exec"),
        (["fs.read"], ["net.http_post"], "file_exfiltration"),
    ]
    
    @classmethod
    def detect_chain(cls, tool_sequence: List[str]) -> tuple[bool, str]:
        """
        Check if tool sequence contains dangerous chain.
        
        Returns:
            (is_dangerous, pattern_name)
        """
        for first_tools, second_tools, pattern_name in cls.BLOCKED_CHAINS:
            # Find indices of first tools
            first_indices = [
                i for i, tool in enumerate(tool_sequence)
                if tool in first_tools
            ]
            
            # Find indices of second tools
            second_indices = [
                i for i, tool in enumerate(tool_sequence)
                if tool in second_tools
            ]
            
            # Check if any first comes before any second
            for first_idx in first_indices:
                for second_idx in second_indices:
                    if first_idx < second_idx:
                        return True, pattern_name
        
        return False, ""


# Export policy rules
RISK_POLICY = {
    "safe_tools": list(ToolRiskClassification.SAFE_TOOLS),
    "restricted_tools": list(ToolRiskClassification.RESTRICTED_TOOLS),
    "dangerous_tools": list(ToolRiskClassification.DANGEROUS_TOOLS),
    "blocked_chains": ChainDetector.BLOCKED_CHAINS,
    "default_classification": "DANGEROUS"  # Fail-closed
}
