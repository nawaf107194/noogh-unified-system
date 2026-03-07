import json
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from gateway.app.core.artifact_registry import get_artifact_registry
from gateway.app.core.auth import AuthContext, require_bearer
from gateway.app.core.jobs import get_job_store
from gateway.app.core.session_store import get_session_store
from gateway.app.plugins.loader import PluginLoader
from gateway.app.plugins.registry import PluginRegistry

# Admin Router
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview")
async def get_overview(request: Request, auth: AuthContext = Depends(require_bearer)):
    """Admin overview."""
    secrets = getattr(request.app.state, "secrets", {})
    data_dir = secrets.get("NOOGH_DATA_DIR")

    # Sessions
    session_store = get_session_store(data_dir=data_dir)
    sessions_count = 0
    if os.path.exists(session_store.base_dir):
        sessions_count = len([f for f in os.listdir(session_store.base_dir) if f.endswith(".json")])

    # Jobs
    job_store = get_job_store(secrets=secrets)
    jobs_count = 0
    if hasattr(job_store, "base_dir") and os.path.exists(job_store.base_dir):
        jobs_count = len(
            [d for d in os.listdir(job_store.base_dir) if os.path.isdir(os.path.join(job_store.base_dir, d))]
        )

    # Plugins
    plugins_count = len(PluginRegistry.get_instance().plugins)

    return {
        "counts": {"sessions": sessions_count, "jobs": jobs_count, "plugins": plugins_count},
        "system_status": "Healthy",
    }


@router.get("/sessions")
async def list_sessions(request: Request, limit: int = 20, auth: AuthContext = Depends(require_bearer)):
    secrets = getattr(request.app.state, "secrets", {})
    data_dir = secrets.get("NOOGH_DATA_DIR")
    session_store = get_session_store(data_dir=data_dir)
    if not os.path.exists(session_store.base_dir):
        return []
    files = sorted(os.listdir(session_store.base_dir), reverse=True)[:limit]
    full_paths = [os.path.join(session_store.base_dir, f) for f in files if f.endswith(".json")]
    full_paths.sort(key=os.path.getmtime, reverse=True)

    results = []
    for p in full_paths:
        try:
            with open(p) as f:
                data = json.load(f)
                results.append(
                    {
                        "session_id": data.get("session_id"),
                        "created_at": data.get("created_at"),
                        "task_count": len(data.get("tasks", [])),
                    }
                )
        except (OSError, json.JSONDecodeError, KeyError):
            pass  # Skip corrupted or invalid session files
    return results


@router.get("/sessions/{session_id}")
async def get_session_detail(request: Request, session_id: str, auth: AuthContext = Depends(require_bearer)):
    secrets = getattr(request.app.state, "secrets", {})
    data_dir = secrets.get("NOOGH_DATA_DIR")
    sess = get_session_store(data_dir=data_dir).get_session(session_id)
    if not sess:
        raise HTTPException(404, "Session not found")
    return sess


@router.get("/jobs")
async def list_jobs(request: Request, limit: int = 20, auth: AuthContext = Depends(require_bearer)):
    secrets = getattr(request.app.state, "secrets", {})
    job_store = get_job_store(secrets=secrets)
    if hasattr(job_store, "base_dir") and os.path.exists(job_store.base_dir):
        dirs = [d for d in os.listdir(job_store.base_dir) if os.path.isdir(os.path.join(job_store.base_dir, d))]
    else:
        return job_store.list_jobs(limit=limit)

    if not dirs:
        return []
    jobs = []
    for d in dirs:
        try:
            j = job_store.get_job(d)
            if j:
                jobs.append(j)
        except (OSError, KeyError, AttributeError):
            pass  # Skip invalid jobs
    jobs.sort(key=lambda x: x.created_at, reverse=True)
    return jobs[:limit]


@router.get("/jobs/{job_id}")
async def get_job_detail(request: Request, job_id: str, auth: AuthContext = Depends(require_bearer)):
    secrets = getattr(request.app.state, "secrets", {})
    j = get_job_store(secrets=secrets).get_job(job_id)
    if not j:
        raise HTTPException(404, "Job not found")
    return j


@router.get("/plugins")
async def list_plugins_admin(auth: AuthContext = Depends(require_bearer)):
    return {"loaded": PluginRegistry.get_instance().plugins, "tools": list(PluginRegistry.get_instance().tools.keys())}


@router.post("/plugins/refresh")
async def refresh_plugins_admin(request: Request, auth: AuthContext = Depends(require_bearer)):
    secrets = getattr(request.app.state, "secrets", {})
    plugin_key = secrets.get("NOOGH_PLUGIN_SIGNING_KEY", "noogh-secure-key")
    loader = PluginLoader(key=plugin_key)
    return loader.load_all()


@router.get("/artifacts")
async def list_artifacts(request: Request, limit: int = 50, auth: AuthContext = Depends(require_bearer)):
    secrets = getattr(request.app.state, "secrets", {})
    data_dir = secrets.get("NOOGH_DATA_DIR")
    return get_artifact_registry(data_dir=data_dir).list_artifacts(limit=limit)


@router.get("/artifacts/{artifact_id}/download")
async def download_artifact(request: Request, artifact_id: str, auth: AuthContext = Depends(require_bearer)):
    secrets = getattr(request.app.state, "secrets", {})
    data_dir = secrets.get("NOOGH_DATA_DIR")
    registry = get_artifact_registry(data_dir=data_dir)
    art = registry.get_artifact(artifact_id)
    if not art:
        raise HTTPException(404, "Artifact not found in registry")

    safe_base = os.path.abspath(data_dir)
    full_path = os.path.abspath(os.path.join(safe_base, art.path))

    if not full_path.startswith(safe_base):
        raise HTTPException(403, "Access Denied: Path traversal detected")

    if not os.path.exists(full_path):
        raise HTTPException(404, "Artifact file missing on disk")

    return FileResponse(full_path, filename=os.path.basename(art.path))
