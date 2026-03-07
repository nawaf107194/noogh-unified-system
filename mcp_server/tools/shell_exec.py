"""
MCP Tool: shell_exec
Standalone module for shell execution via FastMCP.

SECURITY: This module has been hardened to prevent shell injection attacks.
Commands are executed via ProcessActuator with allowlist enforcement.
"""

import shlex
import subprocess
import sys
from pathlib import Path
from typing import List

# Ensure src is in path
sys.path.append(str(Path(__file__).parents[2]))
from config import settings


# SECURITY: Allowed commands whitelist
ALLOWED_COMMANDS = {
    "pwd", "ls", "cat", "head", "tail", "wc", "grep", "find",
    "git", "python", "pip", "pytest", "ruff", "black",
    "echo", "date", "whoami", "hostname",
}


def _is_command_allowed(cmd_parts: List[str]) -> bool:
    """Check if the command is in the allowlist."""
    if not cmd_parts:
        return False
    
    base_cmd = Path(cmd_parts[0]).name  # Handle /usr/bin/ls -> ls
    return base_cmd in ALLOWED_COMMANDS


def shell_exec(cmd: str) -> dict:
    """
    Execute shell commands inside noogh_unified_system repo.
    Returns exit_code, stdout, stderr.
    
    SECURITY HARDENING:
    - shell=False to prevent shell injection
    - Command allowlist enforcement
    - shlex.split for safe argument parsing
    """
    try:
        # Parse command safely
        cmd_parts = shlex.split(cmd)
        
        if not cmd_parts:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": "SECURITY_ERROR: Empty command"
            }
        
        # SECURITY: Check allowlist
        if not _is_command_allowed(cmd_parts):
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": f"SECURITY_BLOCKED: Command '{cmd_parts[0]}' not in allowlist. Allowed: {sorted(ALLOWED_COMMANDS)}"
            }
        
        # Execute with shell=False (SECURE)
        proc = subprocess.run(
            cmd_parts,
            shell=False,  # CRITICAL: Prevent shell injection
            cwd=str(settings.ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=30  # Prevent hanging
        )
        
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:]
        }
        
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "TIMEOUT: Command exceeded 30 second limit"
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"EXECUTION_ERROR: {str(e)}"
        }


# For direct testing
if __name__ == "__main__":
    import json
    
    # Safe command
    result = shell_exec("pwd")
    print("Safe command (pwd):")
    print(json.dumps(result, indent=2))
    
    # Blocked command
    result = shell_exec("rm -rf /")
    print("\nBlocked command (rm):")
    print(json.dumps(result, indent=2))
    
    # Injection attempt (should fail)
    result = shell_exec("ls; rm -rf /")
    print("\nInjection attempt:")
    print(json.dumps(result, indent=2))
