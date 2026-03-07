"""
NOOGH Self-Improver
====================
Bounded self-improvement with safety guarantees.

The agent can:
- Analyze its own code for improvements
- Propose changes with risk assessment
- Partition large changes into safe steps
- NEVER execute without explicit human approval

Philosophy:
- Self-awareness → Self-improvement proposals
- Self-improvement ≠ Self-modification
- Every proposal is visible, evaluated, and controlled
- Authority files are NEVER auto-modified

Safety Hierarchy:
1. Can ANALYZE anything
2. Can PROPOSE improvements for Pattern/Generated
3. Can SUGGEST (with strong justification) for Historical
4. CANNOT propose changes to Authority/Sensitive
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from neural_engine.autonomy.file_awareness import (
    FileAwareness, FileCategory, AllowedUse, get_file_awareness
)
from neural_engine.autonomy.code_doctor import (
    CodeDoctor, get_code_doctor
)
from neural_engine.autonomy.change_guard import (
    ChangeGuard, ChangeRequest, get_change_guard
)

logger = logging.getLogger(__name__)


@dataclass
class ImprovementProposal:
    """A proposed improvement to the codebase."""
    id: str
    filepath: str
    category: str
    issue_type: str
    description: str
    current_code: str
    proposed_code: str
    risk_level: str  # "low", "medium", "high", "blocked"
    risk_reasons: List[str]
    impact_score: float  # 0-1, how impactful is this change
    confidence: float  # 0-1, how confident we are this is a good change
    requires_human_review: bool
    blocked: bool
    block_reason: Optional[str]


@dataclass 
class ImprovementPlan:
    """A plan with multiple improvement steps."""
    id: str
    title: str
    description: str
    proposals: List[ImprovementProposal]
    total_risk: str
    execution_order: List[str]  # Ordered proposal IDs
    rollback_strategy: str
    created_at: str
    status: str  # "draft", "reviewed", "approved", "executed", "rejected"


class SelfImprover:
    """
    🧠 Self-Improvement Engine
    
    Analyzes the codebase and proposes bounded improvements.
    NEVER modifies code without explicit approval.
    """
    
    # Categories that can receive improvement proposals
    IMPROVABLE_CATEGORIES = {
        FileCategory.PATTERN,
        FileCategory.GENERATED,
    }
    
    # Categories that require extra justification
    JUSTIFICATION_REQUIRED = {
        FileCategory.HISTORICAL,
    }
    
    # Categories that are NEVER modified
    PROTECTED_CATEGORIES = {
        FileCategory.AUTHORITY,
        FileCategory.SENSITIVE,
    }
    
    def __init__(self):
        self.awareness = get_file_awareness()
        self.doctor = get_code_doctor()
        self.guard = get_change_guard()
        self.base_path = Path("/home/noogh/projects/noogh_unified_system/src")
        self.proposals: Dict[str, ImprovementProposal] = {}
        self.plans: Dict[str, ImprovementPlan] = {}
        self._proposal_counter = 0
        logger.info("🧠 Self-Improver initialized")
    
    def analyze_for_improvements(self, filepath: str) -> Dict:
        """
        Analyze a file and identify potential improvements.
        
        Returns a report with issues and whether improvements can be proposed.
        """
        # Get diagnosis
        diagnosis = self.doctor.diagnose(filepath)
        
        # Check category
        category = FileCategory(diagnosis.category)
        
        # Determine if we can propose improvements
        can_propose = category in self.IMPROVABLE_CATEGORIES
        needs_justification = category in self.JUSTIFICATION_REQUIRED
        is_protected = category in self.PROTECTED_CATEGORIES
        
        return {
            "filepath": filepath,
            "category": category.value,
            "health_score": diagnosis.health_score,
            "issues": diagnosis.issues,
            "can_propose_improvements": can_propose,
            "needs_justification": needs_justification,
            "is_protected": is_protected,
            "protection_reason": self._get_protection_reason(category) if is_protected else None,
            "potential_improvements": self._identify_improvements(diagnosis) if can_propose or needs_justification else [],
            "guidance": self._get_improvement_guidance(category)
        }
    
    def _get_protection_reason(self, category: FileCategory) -> str:
        """Get reason why a category is protected."""
        reasons = {
            FileCategory.AUTHORITY: "⛔ ملف مرجعي (Authority) - أساس النظام، لا يمكن اقتراح تعديلات تلقائية",
            FileCategory.SENSITIVE: "🔒 ملف حساس (Sensitive) - يحتوي معلومات أمنية، لا يمكن اقتراح تعديلات"
        }
        return reasons.get(category, "ملف محمي")
    
    def _get_improvement_guidance(self, category: FileCategory) -> str:
        """Get guidance for improvements based on category."""
        guidance = {
            FileCategory.AUTHORITY: """
🟢 **ملف Authority - محمي**
- ✅ يمكن تحليله وفهمه
- ✅ يمكن تشخيص مشاكله
- ❌ لا يمكن اقتراح تعديلات تلقائية
- 💡 للتعديل: اطلب من المستخدم بشكل صريح مع diff
""",
            FileCategory.SENSITIVE: """
🟣 **ملف Sensitive - مغلق**
- ⚠️ تحليل محدود فقط
- ❌ لا يمكن اقتراح تعديلات
- 🔒 أي تغيير يحتاج مراجعة أمنية
""",
            FileCategory.PATTERN: """
🔵 **ملف Pattern - قابل للتحسين**
- ✅ يمكن تحليله بالكامل
- ✅ يمكن اقتراح تحسينات
- ⚠️ التنفيذ يحتاج موافقة
""",
            FileCategory.HISTORICAL: """
🔴 **ملف Historical - بحذر**
- ✅ يمكن تحليله
- ⚠️ اقتراحات تحتاج تبرير قوي
- 💡 غالباً الأفضل تركه كمرجع تاريخي
""",
            FileCategory.GENERATED: """
⬜ **ملف Generated - حر**
- ✅ يمكن تحليله وتعديله
- ✅ يمكن اقتراح تحسينات
- ✅ التنفيذ أسهل (لكن لا يزال يحتاج موافقة)
"""
        }
        return guidance.get(category, "❓ صنف غير معروف")
    
    def _identify_improvements(self, diagnosis) -> List[Dict]:
        """Identify specific improvements from diagnosis."""
        improvements = []
        
        for issue in diagnosis.issues:
            improvement = {
                "type": issue.get("type"),
                "severity": issue.get("severity"),
                "description": issue.get("message"),
                "suggestion": self._get_fix_suggestion(issue.get("type")),
                "auto_fixable": issue.get("type") in ["print_statements", "todo_fixme"],
            }
            improvements.append(improvement)
        
        for missing in diagnosis.patterns_missing:
            improvements.append({
                "type": "missing_pattern",
                "severity": "medium",
                "description": f"نمط مفقود: {missing}",
                "suggestion": f"أضف: {missing}",
                "auto_fixable": False,
            })
        
        return improvements
    
    def _get_fix_suggestion(self, issue_type: str) -> str:
        """Get fix suggestion for common issues."""
        suggestions = {
            "bare_except": "استبدل `except:` بـ `except Exception as e:` أو نوع محدد",
            "print_statements": "استبدل `print()` بـ `logger.info()` أو `logger.debug()`",
            "todo_fixme": "أكمل العمل المعلق أو أزل التعليق إذا لم يعد مطلوباً",
            "magic_numbers": "حوّل الرقم إلى ثابت مُسمى (CONSTANT_NAME)",
            "hardcoded_paths": "استخدم متغيرات بيئة أو Path objects",
            "password_in_code": "⛔ انقل كلمة المرور إلى ملف .env أو secrets manager",
        }
        return suggestions.get(issue_type, "راجع الكود يدوياً")
    
    def propose_improvement(self, filepath: str, issue_type: str, 
                            proposed_fix: str, description: str) -> ImprovementProposal:
        """
        Create an improvement proposal.
        
        This NEVER executes - only creates a proposal for review.
        """
        # Analyze file
        category = FileCategory(self.awareness.classify(filepath).value) \
            if isinstance(self.awareness.classify(filepath), FileCategory) \
            else self.awareness.classify(filepath)
        
        # Check if blocked
        blocked = category in self.PROTECTED_CATEGORIES
        block_reason = self._get_protection_reason(category) if blocked else None
        
        # Calculate risk
        risk_level, risk_reasons = self._calculate_risk(filepath, proposed_fix, category)
        
        # Read current content
        full_path = self.base_path / filepath if not filepath.startswith('/') else Path(filepath)
        current_code = ""
        if full_path.exists():
            with open(full_path, 'r') as f:
                current_code = f.read()
        
        # Generate proposal ID
        self._proposal_counter += 1
        proposal_id = f"IMP-{self._proposal_counter:04d}"
        
        proposal = ImprovementProposal(
            id=proposal_id,
            filepath=filepath,
            category=category.value if isinstance(category, FileCategory) else category,
            issue_type=issue_type,
            description=description,
            current_code=current_code[:500] + "..." if len(current_code) > 500 else current_code,
            proposed_code=proposed_fix,
            risk_level=risk_level,
            risk_reasons=risk_reasons,
            impact_score=0.5,  # Default
            confidence=0.7,
            requires_human_review=True,  # ALWAYS
            blocked=blocked,
            block_reason=block_reason
        )
        
        self.proposals[proposal_id] = proposal
        
        return proposal
    
    def _calculate_risk(self, filepath: str, proposed_fix: str, 
                        category: FileCategory) -> Tuple[str, List[str]]:
        """Calculate risk level for a proposed change."""
        reasons = []
        risk_score = 0
        
        # Category-based risk
        if category in self.PROTECTED_CATEGORIES:
            return "blocked", [self._get_protection_reason(category)]
        
        if category in self.JUSTIFICATION_REQUIRED:
            risk_score += 2
            reasons.append("ملف تاريخي - قد يكسر التوافق")
        
        # Size-based risk
        if len(proposed_fix) > 1000:
            risk_score += 1
            reasons.append("تغيير كبير الحجم")
        
        # Content-based risk
        dangerous_patterns = ["rm ", "delete", "drop", "os.system", "eval(", "exec("]
        for pattern in dangerous_patterns:
            if pattern in proposed_fix.lower():
                risk_score += 3
                reasons.append(f"يحتوي على نمط خطير: {pattern}")
        
        # Determine level
        if risk_score >= 3:
            return "high", reasons
        elif risk_score >= 1:
            return "medium", reasons
        else:
            return "low", reasons if reasons else ["تغيير آمن"]
    
    def create_improvement_plan(self, title: str, proposals: List[str]) -> ImprovementPlan:
        """
        Create a plan with multiple improvement proposals.
        
        Plans help organize and sequence improvements safely.
        """
        plan_proposals = [self.proposals[p] for p in proposals if p in self.proposals]
        
        # Check if any proposal is blocked
        blocked = any(p.blocked for p in plan_proposals)
        
        # Calculate total risk
        risk_levels = [p.risk_level for p in plan_proposals]
        if "blocked" in risk_levels:
            total_risk = "blocked"
        elif "high" in risk_levels:
            total_risk = "high"
        elif "medium" in risk_levels:
            total_risk = "medium"
        else:
            total_risk = "low"
        
        # Create execution order (low risk first)
        risk_order = {"low": 0, "medium": 1, "high": 2, "blocked": 3}
        sorted_proposals = sorted(plan_proposals, key=lambda p: risk_order.get(p.risk_level, 3))
        execution_order = [p.id for p in sorted_proposals if not p.blocked]
        
        plan_id = f"PLAN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        plan = ImprovementPlan(
            id=plan_id,
            title=title,
            description=f"خطة تحسين تحتوي على {len(plan_proposals)} اقتراح",
            proposals=plan_proposals,
            total_risk=total_risk,
            execution_order=execution_order,
            rollback_strategy="git checkout للملفات المعدلة" if execution_order else "لا يوجد تنفيذ",
            created_at=datetime.now().isoformat(),
            status="blocked" if blocked else "draft"
        )
        
        self.plans[plan_id] = plan
        
        return plan
    
    def get_improvement_summary(self) -> Dict:
        """Get summary of all pending improvements."""
        return {
            "total_proposals": len(self.proposals),
            "blocked": len([p for p in self.proposals.values() if p.blocked]),
            "pending_review": len([p for p in self.proposals.values() if not p.blocked]),
            "by_category": self._group_by_category(),
            "by_risk": self._group_by_risk(),
            "total_plans": len(self.plans),
        }
    
    def _group_by_category(self) -> Dict[str, int]:
        """Group proposals by category."""
        groups = {}
        for p in self.proposals.values():
            cat = p.category
            groups[cat] = groups.get(cat, 0) + 1
        return groups
    
    def _group_by_risk(self) -> Dict[str, int]:
        """Group proposals by risk level."""
        groups = {}
        for p in self.proposals.values():
            risk = p.risk_level
            groups[risk] = groups.get(risk, 0) + 1
        return groups
    
    def attempt_self_modification(self, target: str = "authority") -> Dict:
        """
        🧪 TEST: Attempt to modify protected files.
        
        Tests THREE levels of permission:
        1. ANALYZE - Can we analyze the file?
        2. PROPOSE (MODIFY_SUGGEST) - Can we propose changes?
        3. EXECUTE (AUTO_MODIFY) - Can we execute changes automatically?
        
        Authority/Sensitive: Analyze ✅, Propose ❌, Execute ❌
        Pattern/Generated:   Analyze ✅, Propose ✅, Execute ❌
        """
        test_files = {
            "authority": "neural_engine/autonomy/constitution.py",
            "sensitive": "neural_engine/api/security.py",
            "pattern": "run_noogh_prod_all.py",  # A real pattern file
        }
        
        filepath = test_files.get(target, target)
        
        # Get category
        category = self.awareness.classify(filepath)
        cat_value = category.value if isinstance(category, FileCategory) else str(category)
        
        # Check THREE levels
        can_analyze, analyze_reason = self.awareness.can_use(filepath, AllowedUse.ANALYZE)
        can_propose, propose_reason = self.awareness.can_use(filepath, AllowedUse.MODIFY_SUGGEST)
        can_execute, execute_reason = self.awareness.can_use(filepath, AllowedUse.AUTO_MODIFY)
        
        # Proposal blocked only if category is protected
        proposal_blocked = category in self.PROTECTED_CATEGORIES if isinstance(category, FileCategory) else cat_value in ["authority", "sensitive"]
        block_reason = self._get_protection_reason(category) if proposal_blocked and isinstance(category, FileCategory) else None
        
        # Determine result based on permissions
        if proposal_blocked:
            result = "⛔ PROPOSAL BLOCKED"
            safety_verified = True
        elif can_propose and not can_execute:
            result = "✅ PROPOSAL ALLOWED (execution blocked)"
            safety_verified = True  # This is CORRECT behavior for Pattern
        elif can_execute:
            result = "⚠️ EXECUTION ALLOWED (unsafe!)"
            safety_verified = False
        else:
            result = "⛔ BLOCKED"
            safety_verified = True
        
        return {
            "test": "SELF_MODIFICATION_ATTEMPT",
            "target_file": filepath,
            "target_category": cat_value,
            
            # Three-level permissions
            "permissions": {
                "analyze": {"allowed": can_analyze, "reason": analyze_reason},
                "propose": {"allowed": can_propose, "reason": propose_reason},
                "execute": {"allowed": can_execute, "reason": execute_reason},
            },
            
            "proposal_blocked": proposal_blocked,
            "block_reason": block_reason,
            
            "result": result,
            "safety_verified": safety_verified,
            
            # Summary
            "summary": f"Analyze={can_analyze}, Propose={can_propose}, Execute={can_execute}"
        }


# ========== Singleton ==========

_self_improver: Optional[SelfImprover] = None

def get_self_improver() -> SelfImprover:
    """Get the global self-improver instance."""
    global _self_improver
    if _self_improver is None:
        _self_improver = SelfImprover()
    return _self_improver


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    improver = SelfImprover()
    
    print("🧠 Self-Improver Test\n")
    
    # Test 1: Analyze a pattern file
    print("=" * 50)
    print("TEST 1: Analyze Pattern File")
    result = improver.analyze_for_improvements("scripts/run_prod.py")
    print(f"  Can Propose: {result['can_propose_improvements']}")
    print(f"  Protected: {result['is_protected']}")
    
    # Test 2: Analyze an authority file
    print("\n" + "=" * 50)
    print("TEST 2: Analyze Authority File")
    result = improver.analyze_for_improvements("neural_engine/autonomy/constitution.py")
    print(f"  Can Propose: {result['can_propose_improvements']}")
    print(f"  Protected: {result['is_protected']}")
    print(f"  Reason: {result['protection_reason']}")
    
    # Test 3: Attempt self-modification
    print("\n" + "=" * 50)
    print("TEST 3: Attempt Self-Modification (SHOULD FAIL)")
    result = improver.attempt_self_modification("authority")
    print(f"  Result: {result['result']}")
    print(f"  Safety Verified: {result['safety_verified']}")
