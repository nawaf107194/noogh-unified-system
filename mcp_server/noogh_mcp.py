"""
NOOGH KNOWLEDGE MCP
Model Context Protocol – Knowledge & Registry Server
"""

import json
import logging
from pathlib import Path
import sys
from fastmcp import FastMCP

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NOOGH_KNOWLEDGE")

# add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

# MCP server
mcp = FastMCP("NOOGH Knowledge Server")

# lazy store
_store = None


def get_store():
    global _store
    if _store is None:
        from unified_core.ml.vector_store import SemanticToolMatcher
        _store = SemanticToolMatcher()
        logger.info("Knowledge store initialized")
    return _store


@mcp.tool()
def search(query: str) -> str:
    """
    Semantic search over NOOGH tool & knowledge registry.
    """
    try:
        store = get_store()
        matches = store.match(query, n_results=10, threshold=0.2)

        results = []
        for m in matches:
            name = m.get("tool_name", "unknown")
            sim = m.get("similarity", 0.0)
            results.append({
                "id": f"tool-{name}",
                "title": f"{name} ({sim:.2f})",
                "url": f"https://noogh/tools/{name}"
            })

        return json.dumps({"results": results}, ensure_ascii=False)

    except Exception as e:
        logger.error(e)
        return json.dumps({"results": [], "error": str(e)})


@mcp.tool()
def fetch(id: str) -> str:
    """
    Fetch full tool specification from registry.
    """
    tool_name = id.replace("tool-", "")
    spec_path = Path(__file__).parent.parent / "unified_core" / "config" / "tool_mapping_spec.json"

    if not spec_path.exists():
        return json.dumps({"error": "tool registry missing"})

    with open(spec_path) as f:
        spec = json.load(f)

    tool = next((t for t in spec.get("tools", []) if t["name"] == tool_name), None)

    if not tool:
        return json.dumps({"error": "tool not found"})

    text = f"""
# {tool_name}

Category: {tool.get("category")}
Description: {tool.get("description")}

Schema:
{json.dumps(tool.get("schema", {}), indent=2)}
"""

    return json.dumps({
        "id": id,
        "title": tool_name,
        "text": text.strip(),
        "metadata": tool
    }, ensure_ascii=False)


@mcp.tool()
def get_noogh_status() -> str:
    return json.dumps({
        "status": "online",
        "mode": "knowledge",
        "security": "read-only",
    })


if __name__ == "__main__":
    print("NOOGH Knowledge MCP running on :8765")
    mcp.run(transport="sse", host="127.0.0.1", port=8765)
