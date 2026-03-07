import json
import time
import uuid
from typing import Any, Dict, Optional


# Legacy simple audit (backward compatible)
def audit_event(kind: str, payload: Dict[str, Any], path: str = "uc3_audit.log") -> str:
    rec = {
        "id": str(uuid.uuid4()),
        "ts": time.time(),
        "kind": kind,
        "payload": payload,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec["id"]


# P1.9: HMAC-signed audit (tamper-proof)
def audit_event_signed(kind: str, payload: Dict[str, Any]) -> str:
    """
    P1.9: Audit event with HMAC signature for tamper detection.

    Returns:
        event_id
    """
    import os

    from gateway.app.security.hmac_logger import get_hmac_logger

    # Get HMAC logger (initialized with secret from env)
    secret = os.getenv("NOOGH_AUDIT_SECRET", "default-insecure-key-change-me").encode("utf-8")
    logger = get_hmac_logger(secret)

    event_id = str(uuid.uuid4())
    event = logger.log_event(event_id=event_id, event_type=kind, payload=payload)

    return event_id


def audit_memory_access(
    operation: str, session_id: str, user_scope: str, query: Optional[str] = None, memory_id: Optional[str] = None
) -> str:
    """
    Audit memory operations for P0.3 compliance with P1.9 HMAC signing.

    Args:
        operation: Type of operation (store/recall)
        session_id: Memory session identifier
        user_scope: User scope (admin/service/readonly)
        query: Search query for recall operations
        memory_id: Memory ID for store operations

    Returns:
        Audit event ID
    """
    return audit_event_signed(
        "memory_access",
        {
            "operation": operation,
            "session_id": session_id,
            "user_scope": user_scope,
            "query": query,
            "memory_id": memory_id,
            "timestamp": time.time(),
        },
    )
