from typing import Any, Dict, List

INTENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "mode": {"type": "string", "enum": ["ANALYZE", "EXECUTE", "OBSERVE"]},  # TRAIN removed
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "summary": {"type": "string", "maxLength": 200},
        "requested_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"action": {"type": "string"}, "args": {"type": "object"}},
                "required": ["action", "args"],
            },
        },
        "safety_notes": {"type": "string", "maxLength": 300},
    },
    "required": ["mode", "confidence", "summary", "requested_actions", "safety_notes"],
}


def extract_actions(mode: str, user_text: str) -> List[Dict[str, Any]]:
    t = user_text.lower()
    actions = []

    if mode == "EXECUTE":
        if "dream" in t or "حلم" in t:
            # default 1 min
            minutes = 1
            for tok in t.split():
                if tok.isdigit():
                    minutes = int(tok)
            actions.append({"action": "dream.start", "args": {"minutes": minutes}})
        if "health" in t or "status" in t or "حالة" in t:
            actions.append({"action": "system.health", "args": {}})
        if "vision" in t or "see" in t or "رؤية" in t:
            actions.append({"action": "vision.process", "args": {}})

    # TRAIN mode removed - ghost endpoints eliminated

    return actions
