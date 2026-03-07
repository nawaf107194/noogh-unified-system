from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Decision:
    allowed: bool
    reason: str
    mode: str
    sanitized_actions: List[Dict[str, Any]]


# Roles: observer/operator/admin
ROLE_SCOPES = {
    "observer": set(["read:logs", "read:metrics", "read:memory"]),
    "operator": set(["read:logs", "read:metrics", "read:memory", "exec:dream", "exec:vision", "exec:memory"]),
    "admin": set(
        ["read:logs", "read:metrics", "read:memory", "exec:dream", "exec:vision", "exec:memory", "exec:admin"]
    ),  # train:model removed
}

# Allowlist for execution actions (No general execution)
ALLOWED_ACTIONS = {
    # EXECUTE actions:
    "dream.start": {"scope": "exec:dream"},
    "dream.stop": {"scope": "exec:dream"},
    "vision.process": {"scope": "exec:vision"},
    "memory.store": {"scope": "exec:memory"},
    "memory.recall": {"scope": "exec:memory"},
    "system.health": {"scope": "read:metrics"},  # health is read-only
    # TRAIN actions removed - ghost endpoints eliminated
}


def evaluate(role: str, mode: str, requested_actions: List[Dict[str, Any]]) -> Decision:
    scopes = ROLE_SCOPES.get(role, set())
    sanitized = []

    # ANALYZE/OBSERVE: Read-only mode, no execution allowd
    if mode in ("ANALYZE", "OBSERVE"):
        return Decision(True, "read-only mode", mode, [])

    # EXECUTE only (TRAIN removed)
    if mode == "EXECUTE":
        for ra in requested_actions:
            action = ra.get("action", "")
            meta = ALLOWED_ACTIONS.get(action)
            if not meta:
                return Decision(False, f"action not allowlisted: {action}", mode, [])
            need = meta["scope"]
            if need not in scopes:
                return Decision(False, f"insufficient scope for {action} (need {need})", mode, [])
            # sanitization hook: arguments can be validated here
            sanitized.append({"action": action, "args": ra.get("args", {})})
        return Decision(True, "allowed", mode, sanitized)

    return Decision(False, "invalid mode", mode, [])
