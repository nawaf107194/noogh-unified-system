#!/usr/bin/env python3
"""
MCP Server for NOOGH API
=========================
Model Context Protocol server that wraps NOOGH API
Compatible with Perplexity, Claude Desktop, and other MCP clients

MCP Spec: https://modelcontextprotocol.io/
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import uvicorn

app = FastAPI(
    title="NOOGH MCP Server",
    version="1.0.0",
    description="Model Context Protocol server for NOOGH Trading System"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
NOOGH_API_URL = "http://localhost:8888"
NOOGH_BEARER_TOKEN = "noogh-project-access-2026-x7k9m2p4"

# MCP Models
class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class Message(BaseModel):
    role: str
    content: str


# MCP Protocol Endpoints
@app.get("/")
async def root():
    """MCP server info"""
    return {
        "name": "NOOGH MCP Server",
        "version": "1.0.0",
        "protocol": "mcp",
        "capabilities": {
            "tools": True,
            "resources": True,
            "prompts": False
        }
    }


@app.get("/mcp/v1/tools")
async def list_tools():
    """
    MCP: List available tools

    Returns all tools that can be called via this MCP server
    """
    tools = [
        {
            "name": "read_file",
            "description": "Read content of a file from NOOGH project",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to project root (e.g., 'agents/autonomous_trading_agent.py')"
                    }
                },
                "required": ["path"]
            }
        },
        {
            "name": "list_files",
            "description": "List all files in NOOGH project or a specific directory",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "File pattern to match (default: '*.py')",
                        "default": "*.py"
                    }
                }
            }
        },
        {
            "name": "search_code",
            "description": "Search for code/text across NOOGH project files",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term"
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to search in (default: '.')",
                        "default": "."
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "File pattern (default: '*.py')",
                        "default": "*.py"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "execute_command",
            "description": "Execute a shell command in NOOGH project",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (optional)"
                    }
                },
                "required": ["command"]
            }
        },
        {
            "name": "get_project_tree",
            "description": "Get NOOGH project directory structure",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "get_system_health",
            "description": "Get NOOGH system health status",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        }
    ]

    return {"tools": tools}


@app.post("/mcp/v1/tools/call")
async def call_tool(tool_call: ToolCall):
    """
    MCP: Execute a tool call

    Routes tool calls to appropriate NOOGH API endpoints
    """
    tool_name = tool_call.name
    args = tool_call.arguments

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {NOOGH_BEARER_TOKEN}"}

        try:
            if tool_name == "read_file":
                # GET /file/{path}
                path = args.get("path", "")
                response = await client.get(
                    f"{NOOGH_API_URL}/file/{path}",
                    headers=headers,
                    timeout=30.0
                )
                data = response.json()

                if "content" in data:
                    return {
                        "result": data["content"],
                        "metadata": {
                            "lines": data.get("lines"),
                            "size_kb": data.get("size_kb")
                        }
                    }
                else:
                    return {"result": data}

            elif tool_name == "list_files":
                # GET /all-files
                pattern = args.get("pattern", "*.py")
                response = await client.get(
                    f"{NOOGH_API_URL}/all-files",
                    params={"pattern": pattern},
                    headers=headers,
                    timeout=30.0
                )
                data = response.json()

                # Format file list
                files = data.get("files", [])
                result = "\n".join([f"{f['path']} ({f['size_kb']} KB)" for f in files])
                return {
                    "result": result,
                    "metadata": {"count": len(files)}
                }

            elif tool_name == "search_code":
                # POST /search
                response = await client.post(
                    f"{NOOGH_API_URL}/search",
                    json={
                        "query": args["query"],
                        "path": args.get("path", "."),
                        "file_pattern": args.get("file_pattern", "*.py")
                    },
                    headers=headers,
                    timeout=30.0
                )
                data = response.json()

                # Format search results
                results = []
                for file_result in data.get("results", []):
                    file_path = file_result["file"]
                    matches = file_result["matches"]
                    results.append(f"\n{file_path} ({file_result['match_count']} matches):")
                    for match in matches[:10]:  # Top 10 per file
                        results.append(f"  Line {match['line_num']}: {match['text']}")

                return {
                    "result": "\n".join(results) if results else "No matches found",
                    "metadata": {
                        "files_matched": data.get("files_matched", 0)
                    }
                }

            elif tool_name == "execute_command":
                # POST /execute
                response = await client.post(
                    f"{NOOGH_API_URL}/execute",
                    json={
                        "command": args["command"],
                        "cwd": args.get("cwd")
                    },
                    headers=headers,
                    timeout=60.0
                )
                data = response.json()

                output = []
                if data.get("stdout"):
                    output.append("STDOUT:\n" + data["stdout"])
                if data.get("stderr"):
                    output.append("STDERR:\n" + data["stderr"])

                return {
                    "result": "\n\n".join(output) if output else "Command completed with no output",
                    "metadata": {
                        "exit_code": data.get("exit_code"),
                        "success": data.get("success")
                    }
                }

            elif tool_name == "get_project_tree":
                # GET /tree
                response = await client.get(
                    f"{NOOGH_API_URL}/tree",
                    headers=headers,
                    timeout=30.0
                )
                data = response.json()

                # Format tree
                tree = data.get("tree", {})
                result = []
                for path, info in sorted(tree.items()):
                    result.append(f"{path}/ ({info['py_count']} Python files)")
                    for file in info.get("py_files", [])[:5]:
                        result.append(f"  - {file}")

                return {
                    "result": "\n".join(result),
                    "metadata": {
                        "total_dirs": len(tree)
                    }
                }

            elif tool_name == "get_system_health":
                # GET /health
                response = await client.get(
                    f"{NOOGH_API_URL}/health",
                    headers=headers,
                    timeout=10.0
                )
                data = response.json()

                return {
                    "result": f"Status: {data.get('status')}\nMode: {data.get('mode')}\nUptime: {data.get('uptime_seconds')}s",
                    "metadata": data
                }

            else:
                raise HTTPException(404, f"Unknown tool: {tool_name}")

        except httpx.HTTPStatusError as e:
            raise HTTPException(e.response.status_code, f"API error: {e}")
        except Exception as e:
            raise HTTPException(500, f"Error calling tool: {str(e)}")


@app.get("/mcp/v1/resources")
async def list_resources():
    """
    MCP: List available resources

    Resources are files/data that can be read
    """
    return {
        "resources": [
            {
                "uri": "noogh://architecture",
                "name": "System Architecture",
                "description": "NOOGH system architecture documentation",
                "mimeType": "text/markdown"
            },
            {
                "uri": "noogh://trading",
                "name": "Trading System",
                "description": "Trading layer files and configuration",
                "mimeType": "application/json"
            }
        ]
    }


@app.get("/mcp/v1/resources/read")
async def read_resource(uri: str):
    """
    MCP: Read a resource by URI
    """
    if uri == "noogh://architecture":
        # Read architecture doc
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {NOOGH_BEARER_TOKEN}"}
            response = await client.get(
                f"{NOOGH_API_URL}/file/docs/ARCHITECTURE.md",
                headers=headers,
                timeout=30.0
            )
            data = response.json()
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/markdown",
                        "text": data.get("content", "")
                    }
                ]
            }
    else:
        raise HTTPException(404, f"Resource not found: {uri}")


if __name__ == "__main__":
    print("🤖 Starting NOOGH MCP Server...")
    print(f"📡 Proxying to: {NOOGH_API_URL}")
    print()
    print("MCP Endpoints:")
    print("  - Tools:     http://localhost:8890/mcp/v1/tools")
    print("  - Resources: http://localhost:8890/mcp/v1/resources")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8890, log_level="info")
