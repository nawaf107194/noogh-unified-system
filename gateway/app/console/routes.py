from typing import Optional, Set

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from gateway.app.core.auth import AuthContext, require_bearer

from .audit import audit_event
from .config import settings
from .context import build_context
from .dispatcher import dispatch_execute  # dispatch_train removed with TRAIN mode
from .intent import extract_actions
from .llm_client import LLMClient
from .policy import evaluate

router = APIRouter(prefix="/uc3", tags=["uc3"])
llm = LLMClient()


def _role_from_scopes(scopes: Set[str]) -> str:
    """Derive role from token scopes (server-side, not client-asserted)."""
    if "*" in scopes:
        return "admin"
    elif any(s.startswith("exec:") for s in scopes):
        return "operator"
    else:
        return "observer"


class ChatReq(BaseModel):
    text: str
    # role removed - derived from token scopes
    include_logs: bool = True
    include_metrics: bool = True
    nonce: Optional[str] = None  # For confirmation step (replaces confirm boolean)


@router.post("/chat")
async def chat(req: ChatReq, auth: AuthContext = Depends(require_bearer)):
    # Derive role from validated token scopes (not client-asserted)
    role = _role_from_scopes(auth.scopes)

    # 1) classify intent
    intent = await llm.classify_intent(req.text)
    mode = intent["mode"]

    # 2) extract actions (optional)
    actions = extract_actions(mode, req.text)
    intent["requested_actions"] = actions

    # 3) policy decision (using derived role)
    decision = evaluate(role, mode, actions)
    audit_id = audit_event("intent", {"role": role, "intent": intent, "decision": decision.__dict__})

    if not decision.allowed:
        return {
            "ok": False,
            "audit_id": audit_id,
            "mode": mode,
            "executed": False,
            "message": f"Denied: {decision.reason}",
            "confirmation_required": False,
        }

    # 4) build context (read-only)
    ctx = await build_context(settings, include_logs=req.include_logs, include_metrics=req.include_metrics)

    # 5) Dispatch based on mode

    # 5) Dispatch based on mode

    # OBSERVE: STRICT LOCAL FACTUALITY. NO LLM.
    if mode == "OBSERVE":
        # 1. Gather Data (or mark UNAVAILABLE)
        metrics = ctx.get("metrics")
        if not metrics:
            # If metrics are missing (whether requested=False or failed), we MUST state UNAVAILABLE
            # We don't default to 0.
            sys_info = "UNAVAILABLE: System metrics not returned from Prometheus/Psutil"
            gpu_info = "UNAVAILABLE: GPU metrics not returned from Neural Engine"
        else:
            # Check individual fields for integrity
            cpu = metrics.get("cpu_util")
            mem = metrics.get("mem_used_gb")
            gpu = metrics.get("gpu_util")
            vram = metrics.get("gpu_vram_mb")

            sys_info = (
                f"CPU: {cpu}% | MEM: {mem}GB used"
                if (cpu is not None and mem is not None)
                else "UNAVAILABLE: Partial system metrics missing"
            )
            # Handle GPU being missing (empty dict) or None
            if gpu is not None and vram is not None:
                gpu_info = f"GPU: {gpu}% (VRAM: {vram}MB)"
            else:
                gpu_info = "UNAVAILABLE: GPU metrics missing"

        # 2. Logs
        gw_logs = ctx.get("gateway_log_tail")
        ne_logs = ctx.get("neural_log_tail")

        gw_log_count = len(gw_logs.splitlines()) if gw_logs else "UNAVAILABLE (Log file empty or missing)"
        ne_log_count = len(ne_logs.splitlines()) if ne_logs else "UNAVAILABLE (Log file empty or missing)"

        # 3. Construct Strict Response
        msg_lines = [
            "MODE: OBSERVE",
            "",
            "ANSWER:",
            "### System Telemetry",
            "- **System Status**: In-Context (Handler executing)",  # Final alignment: refers only to code state
            f"- **Resources**: {sys_info}",
            f"- **Compute**: {gpu_info}",
            "",
            "### Log Status",
            f"- Gateway: {gw_log_count} lines captured",
            f"- Neural Engine: {ne_log_count} lines captured",
            "",
            "DATA SOURCES USED:",
            "- System: psutil / /system/stats",
            f"- Logs: {settings.GATEWAY_LOG}",  # Dynamic path
            "",
            "NEXT ACTIONS:",
            "- Verify raw metrics via /system/stats",
            "- Query specific logs via /system/logs/query",
        ]

        return {
            "ok": True,
            "audit_id": audit_id,
            "mode": mode,
            "executed": False,
            "message": "\n".join(msg_lines),
            "metrics_preview": metrics,
            "debug": None,
            "tools_suggested": [],
            "confidence": 1.0,
            "confirmation_required": False,
        }

    # ANALYZE: Use LLM but enforce strict output
    if mode == "ANALYZE":
        reasoning_result = await llm.reason(req.text, ctx)

        conclusion = reasoning_result.get("conclusion")
        if not conclusion or "Processing complete" in conclusion:
            conclusion = "FAILURE: No valid analysis produced. LLM output did not comply with UC3 format."

        # Verify Mode Adherence (Simple heuristic: must contain 'ANSWER:')
        if "ANSWER:" not in conclusion and "Answer:" not in conclusion:
            # We can try to prepend strictly, or fail. Detailed checking typically needs more parsing.
            # For now, relying on the reasoning_engine to format it, but falling back if it looks like garbage.
            pass

        return {
            "ok": True,
            "audit_id": audit_id,
            "mode": mode,
            "executed": False,
            "message": conclusion,
            "metrics_preview": None,
            "debug": reasoning_result.get("reasoning_trace", []),
            "tools_suggested": reasoning_result.get("suggested_actions", []),
            "confidence": reasoning_result.get("confidence", 0.0),
            "confirmation_required": False,
        }

    # EXECUTE: Require server-verified confirmation
    if mode == "EXECUTE":
        if not req.nonce:
            # PHASE 1: Propose and create pending confirmation
            nonce = request.app.state.confirmation_store.create_pending(
                audit_id=audit_id, actions=decision.sanitized_actions, operator_token=auth.token
            )

            return {
                "ok": True,
                "audit_id": audit_id,
                "mode": mode,
                "executed": False,
                "confirmation_required": True,
                "nonce": nonce,
                "proposed_actions": decision.sanitized_actions,
                "message": f"⚠️ CONFIRMATION REQUIRED\n\nSend this nonce to confirm: {nonce}\n\nProposed actions: {[a['action'] for a in decision.sanitized_actions]}\n\nDO NOT share this nonce.",
            }

        # PHASE 2: Validate confirmation
        validated_actions = request.app.state.confirmation_store.validate_confirmation(
            nonce=req.nonce, operator_token=auth.token
        )

        if not validated_actions:
            raise HTTPException(status_code=403, detail="Invalid, expired, or already-used confirmation nonce")

        # Execute with validated actions
        result = await dispatch_execute(settings, validated_actions)

        audit_event(mode.lower(), {"audit_id": audit_id, "actions": validated_actions, "result": result})
        return {
            "ok": result.get("ok", True),
            "audit_id": audit_id,
            "mode": mode,
            "executed": result.get("executed", True),
            "confirmation_required": False,
            "message": (
                f"✓ {mode} COMPLETE\n\nResults: {result.get('message', 'Operations finished')}"
                if result.get("ok", True)
                else f"✗ {mode} FAILED\n\nSee result for details"
            ),
            "result": result,
            "metrics_preview": None,
            "debug": None,
            "tools_suggested": [],
            "confidence": 1.0,
        }

    # Unknown mode
    return {
        "ok": False,
        "audit_id": audit_id,
        "mode": mode,
        "executed": False,
        "message": f"Unknown mode: {mode}",
        "metrics_preview": None,
        "debug": None,
        "tools_suggested": [],
        "confidence": 0.0,
        "result": {"error": f"Unsupported mode: {mode}"},
        "confirmation_required": False,
    }
