"""
P1.7 - Deterministic Intent Classifier (Mini DSL)
Ensures: Same Input → Same Output (100% deterministic)
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class IntentRule:
    """Single intent classification rule with priority."""

    mode: str
    keywords: List[str]
    priority: int  # Higher number = higher priority
    description: str = ""


# Rules ordered by priority (highest to lowest)
# Priority ensures deterministic behavior when multiple keywords match
INTENT_RULES = [
    # EXECUTE - Highest priority (direct action verbs)
    IntentRule(
        mode="EXECUTE",
        keywords=[
            "run",
            "execute",
            "start",
            "stop",
            "trigger",
            "call",
            "restart",
            "kill",
            "نفذ",
            "شغل",
            "ابدأ",
            "أوقف",
            "نادي",
        ],
        priority=100,
        description="Direct action/execution commands",
    ),
    # OBSERVE - Medium-high priority (status/display verbs)
    IntentRule(
        mode="OBSERVE",
        keywords=[
            "status",
            "health",
            "metrics",
            "show",
            "display",
            "current",
            "get",
            "list",
            "الحالة",
            "الوضع",
            "عرض",
            "اعرض",
            "احصل",
        ],
        priority=80,
        description="Read-only status/metrics queries",
    ),
    # ANALYZE - Medium priority (analytical questions)
    IntentRule(
        mode="ANALYZE",
        keywords=[
            "why",
            "explain",
            "diagnose",
            "analyze",
            "report",
            "investigate",
            "root cause",
            "ليش",
            "لماذا",
            "حلل",
            "فسر",
            "اشرح",
        ],
        priority=60,
        description="Analytical/diagnostic queries",
    ),
]

# Default mode when no keywords match
DEFAULT_MODE = "OBSERVE"
DEFAULT_CONFIDENCE = 0.5


# Exact phrase overrides (highest priority)
# These match full phrases before individual keywords
EXACT_PHRASES = {
    "are there any issues": "OBSERVE",
    "is everything ok": "OBSERVE",
    "what's wrong": "ANALYZE",
    "fix it": "EXECUTE",
    "في مشكلة": "OBSERVE",
    "كل شي تمام": "OBSERVE",
    "ليش كذا": "ANALYZE",
}


def classify_intent_deterministic(query: str) -> Dict:
    """
    100% deterministic intent classification using Mini DSL.

    Guarantees:
    - Same input always produces same output
    - No randomness, no LLM, no heuristics
    - Explicit priority-based conflict resolution

    Args:
        query: User query string

    Returns:
        Dict with mode, confidence, summary, matched_keyword, priority
    """
    query_lower = query.lower().strip()

    # Step 1: Check exact phrase matches (highest priority)
    for phrase, mode in EXACT_PHRASES.items():
        if phrase in query_lower:
            return {
                "mode": mode,
                "confidence": 1.0,
                "summary": f"exact phrase: {phrase}",
                "matched_keyword": phrase,
                "priority": 200,  # Higher than all rules
            }

    # Step 2: Find all matching rules
    matches = []
    for rule in INTENT_RULES:
        for keyword in rule.keywords:
            if keyword in query_lower:
                matches.append((rule, keyword))
                break  # Only need one match per rule

    # Step 3: No matches → use default
    if not matches:
        return {
            "mode": DEFAULT_MODE,
            "confidence": DEFAULT_CONFIDENCE,
            "summary": "no keywords matched, using default",
            "matched_keyword": None,
            "priority": 0,
        }

    # Step 4: Sort by priority (highest first) - deterministic tie-breaking
    matches.sort(key=lambda x: (-x[0].priority, x[1]))  # Sort by priority desc, then keyword alphabetically

    # Step 5: Select highest priority match
    best_rule, matched_keyword = matches[0]

    return {
        "mode": best_rule.mode,
        "confidence": 1.0,  # Always 1.0 for deterministic classification
        "summary": f"matched '{matched_keyword}' (priority={best_rule.priority})",
        "matched_keyword": matched_keyword,
        "priority": best_rule.priority,
    }


def add_custom_rule(mode: str, keywords: List[str], priority: int, description: str = ""):
    """
    Dynamically add a custom rule at runtime.
    Useful for testing or extending the classifier.
    """
    rule = IntentRule(mode=mode, keywords=keywords, priority=priority, description=description)
    INTENT_RULES.append(rule)
    # Re-sort to maintain priority order
    INTENT_RULES.sort(key=lambda r: r.priority, reverse=True)


def get_rules_summary() -> str:
    """Get human-readable summary of all classification rules."""
    lines = ["Intent Classification Rules (Mini DSL):", ""]

    for rule in sorted(INTENT_RULES, key=lambda r: r.priority, reverse=True):
        lines.append(f"Mode: {rule.mode} (Priority: {rule.priority})")
        lines.append(f"  Keywords: {', '.join(rule.keywords[:5])}...")
        lines.append(f"  Description: {rule.description}")
        lines.append("")

    lines.append(f"Default Mode: {DEFAULT_MODE} (when no keywords match)")
    return "\n".join(lines)
