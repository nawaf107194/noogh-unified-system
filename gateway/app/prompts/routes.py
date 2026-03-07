"""
API endpoints for dynamic prompt management.
Allows users to create, activate, and manage custom system prompts.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from gateway.app.core.auth import AuthContext, require_bearer
from gateway.app.prompts.prompt_manager import get_prompt_manager

router = APIRouter(prefix="/prompts", tags=["Prompt Management"])


class CreatePromptRequest(BaseModel):
    name: str
    description: str
    template: str
    category: str
    variables: List[str] = []
    safety_level: str = "standard"
    is_public: bool = True


class RenderPromptRequest(BaseModel):
    prompt_id: str
    variables: Dict[str, Any] = {}


@router.get("/list")
async def list_prompts(category: Optional[str] = None, auth: AuthContext = Depends(require_bearer)):
    """
    List all available prompt templates.

    Query params:
        category: Filter by category (optional)
    """
    manager = get_prompt_manager()
    prompts = manager.list_prompts(category=category)

    return {"ok": True, "prompts": prompts, "total": len(prompts)}


@router.get("/{prompt_id}")
async def get_prompt(prompt_id: str, auth: AuthContext = Depends(require_bearer)):
    """Get a specific prompt template by ID."""
    manager = get_prompt_manager()
    prompt = manager.get_prompt(prompt_id)

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    from dataclasses import asdict

    return {"ok": True, "prompt": asdict(prompt)}


@router.post("/create")
async def create_prompt(request: CreatePromptRequest, auth: AuthContext = Depends(require_bearer)):
    """
    Create a new custom prompt template.

    Safety validation is performed automatically.
    """
    manager = get_prompt_manager()

    try:
        prompt_id = manager.create_prompt(
            name=request.name,
            description=request.description,
            template=request.template,
            category=request.category,
            variables=request.variables,
            author=auth.token[:16],  # Use token prefix as author ID
            safety_level=request.safety_level,
            is_public=request.is_public,
        )

        return {"ok": True, "prompt_id": prompt_id, "message": f"Prompt '{request.name}' created successfully"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate")
async def validate_prompt(template: str, safety_level: str = "standard", auth: AuthContext = Depends(require_bearer)):
    """
    Validate a prompt template for safety.

    Returns validation result without saving.
    """
    manager = get_prompt_manager()
    result = manager.validate_prompt(template, safety_level)

    return {"ok": True, "validation": result}


@router.post("/activate")
async def activate_prompt(prompt_id: str, auth: AuthContext = Depends(require_bearer)):
    """
    Activate a prompt template for use.

    The active prompt will be used for subsequent LLM interactions.
    """
    manager = get_prompt_manager()

    if manager.activate_prompt(prompt_id):
        prompt = manager.get_prompt(prompt_id)

        # Audit activation
        from gateway.app.console.audit import audit_event_signed

        audit_event_signed(
            "prompt_activated",
            {"prompt_id": prompt_id, "prompt_name": prompt.name if prompt else "unknown", "user": auth.token[:16]},
        )

        return {"ok": True, "message": f"Prompt '{prompt.name}' activated", "active_prompt_id": prompt_id}
    else:
        raise HTTPException(status_code=404, detail="Prompt not found")


@router.get("/active")
async def get_active_prompt(auth: AuthContext = Depends(require_bearer)):
    """Get currently active prompt template."""
    manager = get_prompt_manager()

    if manager.active_prompt_id:
        prompt = manager.get_prompt(manager.active_prompt_id)
        if prompt:
            from dataclasses import asdict

            return {"ok": True, "active": True, "prompt": asdict(prompt)}

    return {"ok": True, "active": False, "message": "No active prompt"}


@router.post("/render")
async def render_prompt(request: RenderPromptRequest, auth: AuthContext = Depends(require_bearer)):
    """
    Render a prompt template with variables.

    Useful for previewing before activation.
    """
    manager = get_prompt_manager()
    prompt = manager.get_prompt(request.prompt_id)

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    rendered = prompt.render(**request.variables)

    return {"ok": True, "rendered": rendered, "variables_used": request.variables}


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: str, auth: AuthContext = Depends(require_bearer)):
    """
    Delete a custom prompt template.

    System prompts cannot be deleted.
    """
    manager = get_prompt_manager()

    if manager.delete_prompt(prompt_id):
        return {"ok": True, "message": "Prompt deleted successfully"}
    else:
        raise HTTPException(status_code=403, detail="Cannot delete system prompts or prompt not found")


@router.get("/categories")
async def get_categories(auth: AuthContext = Depends(require_bearer)):
    """Get list of all available categories."""
    manager = get_prompt_manager()

    categories = set(p.category for p in manager.prompts.values())

    return {"ok": True, "categories": sorted(list(categories))}
