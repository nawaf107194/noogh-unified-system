#!/usr/bin/env python3
"""
NOOGH Project API Server v3 - Production Ready
===============================================
سيرفر محسّن باستخدام FastAPI مع:
- Streaming للملفات الكبيرة
- Multi-threading
- Chunked responses
- أمان محسّن
- Health monitoring
- GZIP compression

التثبيت:
  pip install fastapi uvicorn python-multipart

التشغيل:
  python noogh_server_v3.py

أو للـ Production:
  uvicorn noogh_server_v3:app --host 0.0.0.0 --port 8888 --workers 4
"""

import os
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException, Depends, Request
    from fastapi.responses import JSONResponse, StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
except ImportError:
    print("❌ تحتاج تثبّت المكتبات أولاً:")
    print("   pip install fastapi uvicorn python-multipart")
    exit(1)


# ═══════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════
PORT = 8888
BEARER_TOKEN = "noogh-project-access-2026-x7k9m2p4"
PROJECT_ROOT = Path("/home/noogh/projects/noogh_unified_system")
SRC_ROOT = PROJECT_ROOT / "src"

# Key files to expose
KEY_FILES = [
    "agents/autonomous_trading_agent.py",
    "trading/trap_hybrid_engine.py",
    "trading/binance_futures.py",
    "trading/market_analyzer.py",
    "trading/trade_tracker.py",
    "trading/layer_b_filter.py",
    "unified_core/neural_bridge.py",
    "unified_core/agent_daemon.py",
    "unified_core/core/world_model.py",
    "unified_core/core/planning_engine.py",
    "unified_core/core/memory_store.py",
    "tools/adapters/perplexity_adapter.py",
    "strategies/brain_improved_filters.py",
]

EXCLUDE_DIRS = {'__pycache__', '.git', 'logs', 'node_modules', '.venv', 'data', '.mypy_cache', '.pytest_cache'}
EXCLUDE_EXTENSIONS = {'.pyc', '.pyo', '.log', '.tmp'}

# ═══════════════════════════════════════════════════
# App Setup
# ═══════════════════════════════════════════════════
app = FastAPI(
    title="NOOGH Project API",
    version="3.0",
    description="Production-ready API for NOOGH Unified Trading System"
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=500)  # Compress responses > 500 bytes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

security = HTTPBearer()
start_time = time.time()


# ═══════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials


# ═══════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════

@app.get("/")
async def root():
    """Server info and available endpoints."""
    return {
        "name": "NOOGH Project API",
        "version": "3.0",
        "status": "running",
        "uptime_seconds": round(time.time() - start_time),
        "endpoints": {
            "/": "This info (public)",
            "/health": "Health check (public)",
            "/files": "List all key files with metadata (auth required)",
            "/file/{path}": "Get specific file content (auth required)",
            "/summary": "Full project summary with all code (auth required)",
            "/tree": "Project directory tree (auth required)",
            "/search?q=term": "Search code for a term (auth required)",
            "/stats": "Project statistics (auth required)",
        }
    }


@app.get("/health")
async def health():
    """Health check - no auth needed."""
    return {
        "status": "ok",
        "time": datetime.now().isoformat(),
        "uptime_seconds": round(time.time() - start_time),
        "project_root_exists": SRC_ROOT.exists()
    }


@app.get("/tree")
async def project_tree(token: str = Depends(verify_token)):
    """Get project directory structure."""
    tree = {}
    if not SRC_ROOT.exists():
        raise HTTPException(404, "Project root not found")

    for root, dirs, files in os.walk(SRC_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel = os.path.relpath(root, SRC_ROOT)
        py_files = [f for f in files if f.endswith('.py') and not f.startswith('.')]
        other_files = [f for f in files if not f.endswith('.py') and not any(f.endswith(e) for e in EXCLUDE_EXTENSIONS)]

        if py_files or other_files:
            tree[rel] = {
                "py_files": py_files,
                "other_files": other_files[:5],
                "py_count": len(py_files),
                "total_count": len(files)
            }
    return {"tree": tree, "root": str(SRC_ROOT)}


@app.get("/files")
async def list_files(token: str = Depends(verify_token)):
    """List all key files with metadata."""
    files = []
    for rel_path in KEY_FILES:
        full_path = SRC_ROOT / rel_path
        if full_path.exists():
            stat = full_path.stat()
            content = full_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')

            # Extract classes and functions
            classes = [l.strip().split('(')[0].replace('class ', '') for l in lines if l.strip().startswith('class ')]
            functions = [l.strip().split('(')[0].replace('def ', '') for l in lines if l.strip().startswith('def ') and not l.strip().startswith('def _')]

            files.append({
                "path": rel_path,
                "size_kb": round(stat.st_size / 1024, 1),
                "lines": len(lines),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "classes": classes[:10],
                "public_functions": functions[:15],
                "first_docstring": next((l.strip().strip('"\'') for l in lines[:5] if l.strip().startswith(('\"\"\"', "\'\'\'"))), None)
            })

    return {"files": files, "count": len(files)}


@app.get("/file/{file_path:path}")
async def get_file(file_path: str, token: str = Depends(verify_token)):
    """Get content of a specific file."""
    full_path = SRC_ROOT / file_path

    # Security: prevent directory traversal
    try:
        full_path.resolve().relative_to(SRC_ROOT.resolve())
    except ValueError:
        raise HTTPException(403, "Access denied: path outside project")

    if not full_path.exists():
        raise HTTPException(404, f"File not found: {file_path}")

    if full_path.is_dir():
        # List directory contents
        items = []
        for item in sorted(full_path.iterdir()):
            if item.name not in EXCLUDE_DIRS and not item.name.startswith('.'):
                items.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size_kb": round(item.stat().st_size / 1024, 1) if item.is_file() else None
                })
        return {"path": file_path, "type": "directory", "contents": items}

    content = full_path.read_text(encoding='utf-8', errors='ignore')
    return {
        "path": file_path,
        "content": content,
        "lines": len(content.split('\n')),
        "size_kb": round(full_path.stat().st_size / 1024, 1)
    }


@app.get("/summary")
async def summary(token: str = Depends(verify_token)):
    """Full project summary with all key file contents."""
    data = {
        "project": "NOOGH Unified Trading System",
        "description": "Autonomous crypto futures trading system with AI brain, SMC/Order Flow signals, and multi-agent architecture",
        "generated": datetime.now().isoformat(),
        "key_files": {},
        "stats": {"total_lines": 0, "total_files": 0, "total_size_kb": 0}
    }

    for rel_path in KEY_FILES:
        full_path = SRC_ROOT / rel_path
        if full_path.exists():
            content = full_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            size_kb = round(full_path.stat().st_size / 1024, 1)

            data["key_files"][rel_path] = {
                "content": content,
                "lines": len(lines),
                "size_kb": size_kb
            }
            data["stats"]["total_lines"] += len(lines)
            data["stats"]["total_files"] += 1
            data["stats"]["total_size_kb"] += size_kb

    data["stats"]["total_py_files"] = len(list(SRC_ROOT.rglob("*.py"))) if SRC_ROOT.exists() else 0
    return data


@app.get("/search")
async def search_code(q: str, token: str = Depends(verify_token)):
    """Search for a term across all key files."""
    if len(q) < 2:
        raise HTTPException(400, "Search term must be at least 2 characters")

    results = []
    for rel_path in KEY_FILES:
        full_path = SRC_ROOT / rel_path
        if full_path.exists():
            content = full_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            matches = []
            for i, line in enumerate(lines, 1):
                if q.lower() in line.lower():
                    matches.append({"line_num": i, "text": line.strip()[:200]})

            if matches:
                results.append({
                    "file": rel_path,
                    "match_count": len(matches),
                    "matches": matches[:20]  # max 20 matches per file
                })

    return {"query": q, "files_matched": len(results), "results": results}


@app.get("/stats")
async def project_stats(token: str = Depends(verify_token)):
    """Detailed project statistics."""
    if not SRC_ROOT.exists():
        raise HTTPException(404, "Project root not found")

    py_files = list(SRC_ROOT.rglob("*.py"))
    total_lines = 0
    total_size = 0
    largest_files = []

    for f in py_files:
        if any(p in str(f) for p in EXCLUDE_DIRS):
            continue
        size = f.stat().st_size
        lines = len(f.read_text(errors='ignore').split('\n'))
