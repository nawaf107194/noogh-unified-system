"""
Library Import API Endpoint
Bulk import prompts from external collection with smart filtering
"""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from gateway.app.core.auth import AuthContext, require_bearer

router = APIRouter(prefix="/prompts/library", tags=["Prompt Library"])


class ImportRequest(BaseModel):
    categories: Optional[List[str]] = None
    min_quality: float = 0.6
    max_size_kb: int = 50
    limit: int = 100
    tags: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None


@router.post("/import")
async def bulk_import(
    request: ImportRequest, background_tasks: BackgroundTasks, auth: AuthContext = Depends(require_bearer)
):
    """
    Bulk import prompts from the external collection.

    This runs in background and returns immediately.
    """
    from gateway.app.prompts.library import PromptLibrary

    collection_path = "/home/noogh/projects/noogh_unified_system/src/system-prompts-and-models-of-ai-tools-main"

    # Import in background
    def do_import():
        library = PromptLibrary(collection_path)

        results = library.smart_import(
            categories=request.categories,
            min_quality=request.min_quality,
            max_size_kb=request.max_size_kb,
            limit=request.limit,
        )

        # Store results for retrieval
        import json

        with open("data/prompts/last_import.json", "w") as f:
            json.dump(results, f, indent=2)

    background_tasks.add_task(do_import)

    return {
        "ok": True,
        "status": "import_started",
        "message": f"Importing up to {request.limit} prompts in background",
        "check_status": "/prompts/library/status",
    }


@router.get("/status")
async def import_status(auth: AuthContext = Depends(require_bearer)):
    """Get status of last import."""
    import json
    from pathlib import Path

    status_file = Path("data/prompts/last_import.json")

    if not status_file.exists():
        return {"ok": True, "status": "no_imports", "message": "No imports have been run yet"}

    with open(status_file, "r") as f:
        results = json.load(f)

    return {"ok": True, "status": "completed", "results": results}


@router.post("/recommend")
async def recommend_prompts(task: str, limit: int = 5, auth: AuthContext = Depends(require_bearer)):
    """Get prompt recommendations for a task."""
    from gateway.app.prompts.library import PromptLibrary

    collection_path = "/home/noogh/projects/noogh_unified_system/src/system-prompts-and-models-of-ai-tools-main"
    library = PromptLibrary(collection_path)

    recommendations = library.recommend_prompt(task, limit=limit)

    return {"ok": True, "task": task, "recommendations": recommendations}
