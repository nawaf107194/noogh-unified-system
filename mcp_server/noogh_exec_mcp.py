"""
NOOGH EXECUTION MCP
⚠️ LOCAL EXECUTION SERVER
"""

import sys
from pathlib import Path
# Ensure src is in path
sys.path.append(str(Path(__file__).parent.parent))

from config import settings
from config.ports import PORTS
import subprocess
import logging
from typing import Dict
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NOOGH_EXEC")

mcp = FastMCP("NOOGH Execution Server")


@mcp.tool()
def shell_exec(cmd: str) -> Dict:
    """
    Execute shell commands inside NOOGH repo.
    """
    logger.info(f"EXEC: {cmd}")

    proc = subprocess.run(
        cmd,
        shell=True,
        cwd=str(settings.ROOT_DIR),
        capture_output=True,
        text=True
    )

    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:]
    }


if __name__ == "__main__":
    print(f"""
════════════════════════════════════════════════════
🧨 NOOGH EXECUTION MCP (LOCAL ONLY)
════════════════════════════════════════════════════
Port: {PORTS.MCP_EXECUTION}
Transport: SSE
Scope: {settings.ROOT_DIR}
════════════════════════════════════════════════════
""")

    mcp.run(
        transport="sse",
        host="127.0.0.1",
        port=PORTS.MCP_EXECUTION
    )
