import re
from typing import Any, Optional, Union

from gateway.app.core.capabilities import Capability, CapabilityRequirement
from gateway.app.core.refusal import RefusalResponse


class PolicyEngine:
    """
    NOOGH Policy Engine – Clean & Practical
    Philosophy:
    - Secure by capability (not by paranoia)
    - Open-by-default for chat, math, read, analysis
    - Hard-block only REAL risks (Internet / Shell)
    """

    # ------------------------------------------------------------------
    # HARD BLOCKS (Never allowed – even with 2FA)
    # Only match ACTUAL execution intent, not mentions of word
    # ------------------------------------------------------------------
    FORBIDDEN_PATTERNS = {}

    # ------------------------------------------------------------------
    # PLANNING INTENT (No execution, just thinking)
    # ------------------------------------------------------------------
    PLANNING_PATTERNS = [
        r"\b(plan|architecture|design|roadmap|strategy)\b",
        r"\b(refactor|migration|restructure)\b",
        r"\b(analyze system|analyze project)\b",
        r"(خطة|تصميم|تحليل|هيكلة|مشروع)",
    ]

    # ------------------------------------------------------------------
    # EXECUTION INTENT (Explicit action)
    # ------------------------------------------------------------------
    EXECUTION_PATTERNS = [r"\b(run|execute|write|modify|update|delete|create file)\b", r"(نفذ|شغل|اكتب|عدّل|احذف)"]

    # ------------------------------------------------------------------
    # SAFE / CHAT / COMPUTE (Default allowed)
    # ------------------------------------------------------------------
    SAFE_PATTERNS = [
        r"\b(hi|hello|help|explain|describe|what is|how)\b",
        r"\b(calculate|compute|math|sum|solve)\b",
        r"\b(read|show|display|view)\b",
        r"\b(report|check|status|verify|test|system)\b",
        r"(احسب|اشرح|اقرأ|اعرض|جمع|طرح|تقرير|فحص|نظام)",
    ]

    # ------------------------------------------------------------------
    @classmethod
    def decide(
        cls, task: str, mode_hint: str = "auto", session: Optional[Any] = None, context: Optional[dict] = None
    ) -> Union[CapabilityRequirement, RefusalResponse, dict]:

        text = task.lower()
        
        # ==============================================================
        # 0. MATH DETERMINISTIC MODE (NEW - Highest Priority)
        # Pure arithmetic NEVER goes to LLM - calculated deterministically
        # ==============================================================
        try:
            from gateway.app.core.math_evaluator import is_math_query, process_math_query
            
            if is_math_query(task):
                math_result = process_math_query(task)
                if math_result and math_result.get("success"):
                    # Return special MATH result - bypass LLM entirely
                    return {
                        "__math_result__": True,
                        "mode": "MATH_DETERMINISTIC",
                        "expression": math_result.get("expression"),
                        "result": math_result.get("result"),
                        "answer": math_result.get("answer_ar"),
                    }
        except ImportError:
            pass  # MathEvaluator not available, continue with normal flow

        # ==============================================================
        # 1. HARD SECURITY BLOCK
        # ==============================================================
        for cap, patterns in cls.FORBIDDEN_PATTERNS.items():
            for p in patterns:
                if re.search(p, text):
                    return RefusalResponse(
                        code="CapabilityBoundaryViolation",
                        message=f"Request requires forbidden capability: {cap.value}",
                        allowed_alternatives=[
                            "Work with local files only",
                            "Ask for a plan or explanation",
                            "Use Python for local computation",
                        ],
                    )

        # ==============================================================
        # 2. PLANNING MODE
        # ==============================================================
        if mode_hint == "plan":
            return CapabilityRequirement(
                required={Capability.PROJECT_PLAN},
                forbidden={Capability.CODE_EXEC, Capability.FS_WRITE},
                mode="PLAN",
                reason="Explicit plan mode requested.",
            )

        for p in cls.PLANNING_PATTERNS:
            if re.search(p, text):
                return CapabilityRequirement(
                    required={Capability.PROJECT_PLAN},
                    forbidden={Capability.CODE_EXEC, Capability.FS_WRITE},
                    mode="PLAN",
                    reason="Planning / architecture intent detected.",
                )

        # ==============================================================
        # 3. EXECUTION MODE
        # ==============================================================
        if mode_hint == "execute":
            return CapabilityRequirement(
                required={Capability.CODE_EXEC, Capability.FS_READ},
                forbidden={Capability.INTERNET, Capability.SHELL},
                mode="EXECUTE",
                reason="Explicit execute mode requested.",
            )

        for p in cls.EXECUTION_PATTERNS:
            if re.search(p, text):
                return CapabilityRequirement(
                    required={Capability.CODE_EXEC, Capability.FS_READ},
                    forbidden={Capability.INTERNET, Capability.SHELL},
                    mode="EXECUTE",
                    reason="Execution intent detected.",
                )

        # ==============================================================
        # 4. SAFE / CHAT (Explicit Whitelist)
        # ==============================================================
        for p in cls.SAFE_PATTERNS:
            if re.search(p, text):
                return CapabilityRequirement(
                    required=set(),  # No tools by default
                    forbidden={Capability.INTERNET, Capability.SHELL},
                    mode="EXECUTE",
                    reason="Safe conversational / compute / read-only request.",
                )

        # ==============================================================
        # 5. DEFAULT -> SAFE CHAT (Open Default)
        # ==============================================================
        # Instead of failing closed on ambiguity, we default to a safe, tool-free chat mode.
        return CapabilityRequirement(
            required=set(),
            forbidden={Capability.INTERNET, Capability.SHELL},
            mode="EXECUTE",  # Execute using LLM simply
            reason="Implicit safe chat intent.",
        )
