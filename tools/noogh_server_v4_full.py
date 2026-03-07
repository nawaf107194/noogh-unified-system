#!/usr/bin/env python3
"""
NOOGH Project API Server v4 - FULL ACCESS
==========================================
سيرفر كامل بدون قيود مع:
- قراءة جميع الملفات (بدون تحديد)
- كتابة وتعديل الملفات
- حذف الملفات
- تنفيذ الأوامر
- CORS كامل
- GZIP compression

⚠️ تحذير أمني: هذا السيرفر يعطي وصول كامل للنظام!
استخدمه فقط في بيئة آمنة ومع Bearer Token قوي.

التثبيت:
  pip install fastapi uvicorn python-multipart

التشغيل:
  python noogh_server_v4_full.py
"""

import os
import json
import time
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from fastapi import FastAPI, HTTPException, Depends, Request, Body
    from fastapi.responses import JSONResponse, StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from pydantic import BaseModel
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

EXCLUDE_DIRS = {'__pycache__', '.git', 'node_modules', '.venv', '.mypy_cache', '.pytest_cache'}
EXCLUDE_EXTENSIONS = {'.pyc', '.pyo'}

# ═══════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════
class WriteFileRequest(BaseModel):
    content: str
    encoding: str = "utf-8"

class ExecuteCommandRequest(BaseModel):
    command: str
    cwd: Optional[str] = None
    timeout: int = 30

class SearchRequest(BaseModel):
    query: str
    path: str = "."
    file_pattern: str = "*.py"

# ═══════════════════════════════════════════════════
# App Setup
# ═══════════════════════════════════════════════════
app = FastAPI(
    title="NOOGH Project API - Full Access",
    version="4.0",
    description="Full access API for NOOGH System with read/write/execute capabilities"
)

# Middleware - Allow ALL methods
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],  # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
    allow_credentials=True,
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
# Helper Functions
# ═══════════════════════════════════════════════════
def is_safe_path(path: Path, base: Path) -> bool:
    """Check if path is within base directory (prevent directory traversal)."""
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


# ═══════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════

@app.get("/")
async def root():
    """Server info and available endpoints."""
    return {
        "name": "NOOGH Project API - Full Access",
        "version": "4.0",
        "status": "running",
        "uptime_seconds": round(time.time() - start_time),
        "mode": "FULL_ACCESS",
        "warning": "⚠️ This server has full read/write/execute access",
        "endpoints": {
            "GET /": "This info (public)",
            "GET /health": "Health check (public)",
            "GET /tree": "Project directory tree (auth)",
            "GET /file/{path}": "Read file or list directory (auth)",
            "POST /file/{path}": "Write/create file (auth)",
            "DELETE /file/{path}": "Delete file (auth)",
            "POST /execute": "Execute shell command (auth)",
            "POST /search": "Search files (auth)",
            "GET /all-files": "List all Python files (auth)",
        }
    }


@app.get("/health")
async def health():
    """Health check - no auth needed."""
    return {
        "status": "ok",
        "time": datetime.now().isoformat(),
        "uptime_seconds": round(time.time() - start_time),
        "project_root_exists": SRC_ROOT.exists(),
        "mode": "FULL_ACCESS"
    }


@app.get("/tree")
async def project_tree(token: str = Depends(verify_token)):
    """Get complete project directory structure."""
    tree = {}
    if not SRC_ROOT.exists():
        raise HTTPException(404, "Project root not found")

    for root, dirs, files in os.walk(SRC_ROOT):
        # Filter excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        rel = os.path.relpath(root, SRC_ROOT)
        py_files = [f for f in files if f.endswith('.py') and not f.startswith('.')]
        other_files = [f for f in files if not f.endswith('.py') and not any(f.endswith(e) for e in EXCLUDE_EXTENSIONS)]

        if py_files or other_files:
            tree[rel] = {
                "py_files": py_files,
                "other_files": other_files,
                "py_count": len(py_files),
                "total_count": len(files)
            }

    return {
        "tree": tree,
        "root": str(SRC_ROOT),
        "total_dirs": len(tree)
    }


@app.get("/all-files")
async def all_files(token: str = Depends(verify_token), pattern: str = "*.py"):
    """List all files matching pattern."""
    if not SRC_ROOT.exists():
        raise HTTPException(404, "Project root not found")

    files = []
    for file_path in SRC_ROOT.rglob(pattern):
        if any(excl in str(file_path) for excl in EXCLUDE_DIRS):
            continue

        stat = file_path.stat()
        rel_path = file_path.relative_to(SRC_ROOT)

        files.append({
            "path": str(rel_path),
            "size_kb": round(stat.st_size / 1024, 1),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_file": file_path.is_file()
        })

    return {
        "files": files,
        "count": len(files),
        "pattern": pattern
    }


@app.get("/file/{file_path:path}")
async def read_file(file_path: str, token: str = Depends(verify_token)):
    """Read file content or list directory contents."""
    full_path = SRC_ROOT / file_path

    # Security check
    if not is_safe_path(full_path, SRC_ROOT):
        raise HTTPException(403, "Access denied: path outside project")

    if not full_path.exists():
        raise HTTPException(404, f"File not found: {file_path}")

    # If directory, list contents
    if full_path.is_dir():
        items = []
        for item in sorted(full_path.iterdir()):
            if item.name.startswith('.'):
                continue

            items.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size_kb": round(item.stat().st_size / 1024, 1) if item.is_file() else None,
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            })

        return {
            "path": file_path,
            "type": "directory",
            "contents": items,
            "count": len(items)
        }

    # Read file
    try:
        content = full_path.read_text(encoding='utf-8', errors='ignore')
        return {
            "path": file_path,
            "type": "file",
            "content": content,
            "lines": len(content.split('\n')),
            "size_kb": round(full_path.stat().st_size / 1024, 1),
            "modified": datetime.fromtimestamp(full_path.stat().st_mtime).isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Error reading file: {str(e)}")


@app.post("/file/{file_path:path}")
async def write_file(
    file_path: str,
    request: WriteFileRequest,
    token: str = Depends(verify_token)
):
    """Write or create a file."""
    full_path = SRC_ROOT / file_path

    # Security check
    if not is_safe_path(full_path, SRC_ROOT):
        raise HTTPException(403, "Access denied: path outside project")

    # Create parent directories if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Backup if file exists
        backup_path = None
        if full_path.exists():
            backup_path = full_path.with_suffix(full_path.suffix + '.backup')
            import shutil
            shutil.copy2(full_path, backup_path)

        # Write file
        full_path.write_text(request.content, encoding=request.encoding)

        return {
            "status": "success",
            "path": file_path,
            "action": "updated" if backup_path else "created",
            "size_kb": round(full_path.stat().st_size / 1024, 1),
            "lines": len(request.content.split('\n')),
            "backup": str(backup_path.relative_to(SRC_ROOT)) if backup_path else None
        }

    except Exception as e:
        raise HTTPException(500, f"Error writing file: {str(e)}")


@app.delete("/file/{file_path:path}")
async def delete_file(file_path: str, token: str = Depends(verify_token)):
    """Delete a file or directory."""
    full_path = SRC_ROOT / file_path

    # Security check
    if not is_safe_path(full_path, SRC_ROOT):
        raise HTTPException(403, "Access denied: path outside project")

    if not full_path.exists():
        raise HTTPException(404, f"File not found: {file_path}")

    try:
        if full_path.is_dir():
            import shutil
            shutil.rmtree(full_path)
            return {
                "status": "success",
                "action": "deleted_directory",
                "path": file_path
            }
        else:
            full_path.unlink()
            return {
                "status": "success",
                "action": "deleted_file",
                "path": file_path
            }

    except Exception as e:
        raise HTTPException(500, f"Error deleting: {str(e)}")


@app.post("/execute")
async def execute_command(
    request: ExecuteCommandRequest,
    token: str = Depends(verify_token)
):
    """Execute a shell command."""
    cwd = request.cwd or str(SRC_ROOT)

    # Security: ensure cwd is within project
    cwd_path = Path(cwd).resolve()
    if not is_safe_path(cwd_path, PROJECT_ROOT):
        raise HTTPException(403, "Working directory must be within project")

    try:
        result = subprocess.run(
            request.command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=request.timeout
        )

        return {
            "status": "completed",
            "command": request.command,
            "cwd": cwd,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(408, f"Command timeout after {request.timeout}s")
    except Exception as e:
        raise HTTPException(500, f"Error executing command: {str(e)}")


@app.post("/search")
async def search_files(
    request: SearchRequest,
    token: str = Depends(verify_token)
):
    """Search for text in files."""
    search_path = SRC_ROOT / request.path

    if not is_safe_path(search_path, SRC_ROOT):
        raise HTTPException(403, "Search path must be within project")

    if not search_path.exists():
        raise HTTPException(404, "Search path not found")

    results = []
    for file_path in search_path.rglob(request.file_pattern):
        if any(excl in str(file_path) for excl in EXCLUDE_DIRS):
            continue

        if not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            matches = []

            for i, line in enumerate(lines, 1):
                if request.query.lower() in line.lower():
                    matches.append({
                        "line_num": i,
                        "text": line.strip()[:200]
                    })

            if matches:
                results.append({
                    "file": str(file_path.relative_to(SRC_ROOT)),
                    "match_count": len(matches),
                    "matches": matches[:50]  # max 50 matches per file
                })

        except Exception:
            continue

    return {
        "query": request.query,
        "path": request.path,
        "pattern": request.file_pattern,
        "files_matched": len(results),
        "results": results
    }


# ═══════════════════════════════════════════════════
# Run Server
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    print("🚀 Starting NOOGH Full Access Server v4...")
    print(f"📁 Project Root: {SRC_ROOT}")
    print(f"🔑 Bearer Token: {BEARER_TOKEN}")
    print(f"⚠️  WARNING: Full read/write/execute access enabled!")
    print(f"🌐 Server will run on: http://0.0.0.0:{PORT}")
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
