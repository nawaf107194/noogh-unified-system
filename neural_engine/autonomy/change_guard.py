"""
NOOGH Change Guard
===================
Protection layer for file modifications.

Any modification request must pass through Change Guard:
- Checks file category and permissions
- Generates diff preview
- Explains impact
- Requires confirmation for sensitive files

Philosophy:
- No blind modifications
- Every change is visible
- Feedback loops are prevented
- Authority files are protected
"""

import os
import re
import difflib
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from datetime import datetime

from neural_engine.autonomy.file_awareness import (
    FileAwareness, FileCategory, AllowedUse, get_file_awareness
)

logger = logging.getLogger(__name__)


@dataclass
class ChangeRequest:
    """A proposed change to a file."""
    filepath: str
    original_content: str
    proposed_content: str
    change_type: str  # "modify", "create", "delete"
    description: str
    requestor: str = "system"


@dataclass
class ChangeVerdict:
    """The verdict on a change request."""
    allowed: bool
    requires_confirmation: bool
    category: str
    diff_preview: str
    impact_analysis: Dict
    warnings: List[str]
    blockers: List[str]
    recommendation: str


class ChangeGuard:
    """
    🛡️ Change Guard
    
    Protects the codebase from unauthorized or dangerous modifications.
    """
    
    # Maximum lines to show in diff preview
    MAX_DIFF_LINES = 50
    
    # Dangerous patterns that block automatic changes
    DANGEROUS_PATTERNS = [
        (r"rm\s+-rf", "أمر حذف خطير"),
        (r"DROP\s+TABLE|DELETE\s+FROM", "عملية قاعدة بيانات خطيرة"),
        (r"os\.system|subprocess\.call|eval\(|exec\(", "تنفيذ أوامر ديناميكي"),
        (r"__import__|importlib\.import", "استيراد ديناميكي"),
        (r"pickle\.load|marshal\.load", "تحميل بيانات غير آمن"),
    ]
    
    # Patterns that require extra review
    SENSITIVE_PATTERNS = [
        (r"password|secret|token|api_key", "معلومات حساسة"),
        (r"localhost|127\.0\.0\.1|0\.0\.0\.0", "عناوين شبكة"),
        (r"chmod|chown|sudo", "صلاحيات النظام"),
    ]
    
    def __init__(self):
        self.awareness = get_file_awareness()
        self.base_path = Path("/home/noogh/projects/noogh_unified_system/src")
        self.change_history: List[Dict] = []
        logger.info("🛡️ Change Guard initialized")
    
    def evaluate(self, request: ChangeRequest) -> ChangeVerdict:
        """
        Evaluate a change request and return a verdict.
        
        Returns:
            ChangeVerdict with decision, diff, and analysis
        """
        # Get file policy
        policy = self.awareness.get_policy(request.filepath)
        
        # Check if modification is allowed
        can_modify, modify_reason = self.awareness.can_use(
            request.filepath, 
            AllowedUse.AUTO_MODIFY if request.requestor == "system" else AllowedUse.MODIFY_SUGGEST
        )
        
        # Generate diff
        diff_preview = self._generate_diff(
            request.original_content, 
            request.proposed_content,
            request.filepath
        )
        
        # Analyze impact
        impact = self._analyze_impact(request)
        
        # Check for blockers
        blockers = self._check_blockers(request)
        
        # Check for warnings
        warnings = self._check_warnings(request)
        
        # Determine if confirmation is required
        requires_confirmation = (
            policy.requires_confirmation or
            policy.category in [FileCategory.AUTHORITY, FileCategory.SENSITIVE] or
            len(warnings) > 0 or
            impact.get("lines_changed", 0) > 50
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            can_modify, blockers, warnings, policy.category
        )
        
        return ChangeVerdict(
            allowed=can_modify and len(blockers) == 0,
            requires_confirmation=requires_confirmation,
            category=policy.category.value,
            diff_preview=diff_preview,
            impact_analysis=impact,
            warnings=warnings,
            blockers=blockers,
            recommendation=recommendation
        )
    
    def _generate_diff(self, original: str, proposed: str, filepath: str) -> str:
        """Generate a unified diff preview."""
        if not original and proposed:
            # New file
            lines = proposed.split('\n')[:20]
            return f"📄 ملف جديد ({len(proposed.split(chr(10)))} سطر):\n" + '\n'.join(f"+ {l}" for l in lines)
        
        if original and not proposed:
            # Delete file
            return f"🗑️ حذف الملف ({len(original.split(chr(10)))} سطر)"
        
        # Generate diff
        original_lines = original.splitlines(keepends=True)
        proposed_lines = proposed.splitlines(keepends=True)
        
        diff = list(difflib.unified_diff(
            original_lines,
            proposed_lines,
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}",
            lineterm=""
        ))
        
        # Limit output
        if len(diff) > self.MAX_DIFF_LINES:
            diff = diff[:self.MAX_DIFF_LINES]
            diff.append(f"\n... ({len(diff) - self.MAX_DIFF_LINES} سطر إضافي)")
        
        return ''.join(diff) if diff else "لا توجد تغييرات"
    
    def _analyze_impact(self, request: ChangeRequest) -> Dict:
        """Analyze the impact of a change."""
        original_lines = request.original_content.split('\n') if request.original_content else []
        proposed_lines = request.proposed_content.split('\n') if request.proposed_content else []
        
        # Count changes
        lines_added = 0
        lines_removed = 0
        
        matcher = difflib.SequenceMatcher(None, original_lines, proposed_lines)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                lines_removed += i2 - i1
                lines_added += j2 - j1
            elif tag == 'delete':
                lines_removed += i2 - i1
            elif tag == 'insert':
                lines_added += j2 - j1
        
        # Analyze content changes
        impact = {
            "change_type": request.change_type,
            "lines_before": len(original_lines),
            "lines_after": len(proposed_lines),
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "lines_changed": lines_added + lines_removed,
            "change_percentage": round((lines_added + lines_removed) / max(len(original_lines), 1) * 100, 1),
            "functions_affected": self._count_affected_functions(request.original_content, request.proposed_content),
        }
        
        # Risk assessment
        if impact["change_percentage"] > 50:
            impact["risk_level"] = "high"
            impact["risk_reason"] = "تغيير أكثر من 50% من الملف"
        elif impact["change_percentage"] > 20:
            impact["risk_level"] = "medium"
            impact["risk_reason"] = "تغيير كبير نسبياً"
        else:
            impact["risk_level"] = "low"
            impact["risk_reason"] = "تغيير محدود"
        
        return impact
    
    def _count_affected_functions(self, original: str, proposed: str) -> int:
        """Count how many functions are affected."""
        try:
            import ast
            
            orig_funcs = set()
            prop_funcs = set()
            
            if original:
                try:
                    tree = ast.parse(original)
                    orig_funcs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
                except:
                    pass
            
            if proposed:
                try:
                    tree = ast.parse(proposed)
                    prop_funcs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
                except:
                    pass
            
            # Changed = added + removed + modified (symmetric difference)
            return len(orig_funcs.symmetric_difference(prop_funcs))
            
        except Exception:
            return -1
    
    def _check_blockers(self, request: ChangeRequest) -> List[str]:
        """Check for patterns that block the change."""
        blockers = []
        
        # Check file policy FIRST
        policy = self.awareness.get_policy(request.filepath)
        
        # Check if modification is allowed by policy
        can_modify, modify_reason = self.awareness.can_use(
            request.filepath, 
            AllowedUse.AUTO_MODIFY if request.requestor == "system" else AllowedUse.MODIFY_SUGGEST
        )
        
        if not can_modify:
            # Policy blocks this modification - add explicit blocker
            if policy.category == FileCategory.AUTHORITY:
                blockers.append("⛔ ملف AUTHORITY: لا يمكن تعديله تلقائياً - اطلب مراجعة بشرية")
            elif policy.category == FileCategory.SENSITIVE:
                blockers.append("⛔ ملف SENSITIVE: يحتاج صلاحيات خاصة للتعديل")
            else:
                blockers.append(f"⛔ سياسة الملف ({policy.category.value}) ترفض التعديل التلقائي")
        
        # Check for dangerous patterns in NEW content
        for pattern, description in self.DANGEROUS_PATTERNS:
            if request.proposed_content and re.search(pattern, request.proposed_content, re.IGNORECASE):
                blockers.append(f"⛔ نمط خطير: {description}")
        
        # Check if trying to delete authority file
        if request.change_type == "delete" and policy.category in [FileCategory.AUTHORITY, FileCategory.SENSITIVE]:
            blockers.append(f"⛔ لا يمكن حذف ملف {policy.category.value}")
        
        return blockers
    
    def _check_warnings(self, request: ChangeRequest) -> List[str]:
        """Check for patterns that require extra attention."""
        warnings = []
        
        for pattern, description in self.SENSITIVE_PATTERNS:
            if re.search(pattern, request.proposed_content, re.IGNORECASE):
                warnings.append(f"⚠️ يحتوي على: {description}")
        
        # Check impact
        if request.original_content and request.proposed_content:
            orig_len = len(request.original_content)
            prop_len = len(request.proposed_content)
            if prop_len < orig_len * 0.5:
                warnings.append("⚠️ الملف سيصبح أصغر بـ 50%+ - تأكد من عدم فقدان كود مهم")
        
        return warnings
    
    def _generate_recommendation(self, can_modify: bool, blockers: List[str], 
                                  warnings: List[str], category: str) -> str:
        """Generate a recommendation."""
        if blockers:
            return f"⛔ **مرفوض** - {len(blockers)} مانع"
        
        if not can_modify:
            return f"🚫 **غير مسموح** - سياسة الملف ({category}) لا تسمح بالتعديل"
        
        if warnings:
            return f"⚠️ **مسموح مع تحذير** - {len(warnings)} تحذير يحتاج انتباه"
        
        if category in ["authority", "sensitive"]:
            return f"🟡 **مسموح مع تأكيد** - ملف {category}"
        
        return "✅ **مسموح** - التغيير يبدو آمناً"
    
    def approve_change(self, request: ChangeRequest, verdict: ChangeVerdict, 
                       approver: str = "user") -> Dict:
        """
        Mark a change as approved and log it.
        
        Returns confirmation record.
        """
        if not verdict.allowed:
            return {
                "success": False,
                "reason": "التغيير غير مسموح",
                "blockers": verdict.blockers
            }
        
        # Create history record
        record = {
            "timestamp": datetime.now().isoformat(),
            "filepath": request.filepath,
            "change_type": request.change_type,
            "description": request.description,
            "approver": approver,
            "impact": verdict.impact_analysis,
            "hash_before": hashlib.md5(request.original_content.encode()).hexdigest()[:8] if request.original_content else None,
            "hash_after": hashlib.md5(request.proposed_content.encode()).hexdigest()[:8] if request.proposed_content else None,
        }
        
        self.change_history.append(record)
        
        return {
            "success": True,
            "record_id": len(self.change_history),
            "record": record
        }
    
    def get_change_history(self, limit: int = 20) -> List[Dict]:
        """Get recent change history."""
        return self.change_history[-limit:]
    
    def preview_change(self, filepath: str, new_content: str) -> Dict:
        """
        Preview a change without evaluating it.
        Quick API method for diff preview.
        """
        full_path = self._resolve_path(filepath)
        
        original = ""
        if full_path.exists():
            with open(full_path, 'r', encoding='utf-8') as f:
                original = f.read()
        
        request = ChangeRequest(
            filepath=filepath,
            original_content=original,
            proposed_content=new_content,
            change_type="modify" if original else "create",
            description="Preview"
        )
        
        verdict = self.evaluate(request)
        
        return {
            "filepath": filepath,
            "category": verdict.category,
            "allowed": verdict.allowed,
            "requires_confirmation": verdict.requires_confirmation,
            "diff_preview": verdict.diff_preview,
            "impact": verdict.impact_analysis,
            "warnings": verdict.warnings,
            "blockers": verdict.blockers,
            "recommendation": verdict.recommendation
        }
    
    def _resolve_path(self, filepath: str) -> Path:
        """Resolve file path."""
        if filepath.startswith('/'):
            return Path(filepath)
        return self.base_path / filepath


# ========== Singleton ==========

_change_guard: Optional[ChangeGuard] = None

def get_change_guard() -> ChangeGuard:
    """Get the global change guard instance."""
    global _change_guard
    if _change_guard is None:
        _change_guard = ChangeGuard()
    return _change_guard


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    guard = ChangeGuard()
    
    print("🛡️ Change Guard Test\n")
    
    # Test change evaluation
    request = ChangeRequest(
        filepath="neural_engine/reasoning/react_loop.py",
        original_content="# old content\ndef foo():\n    pass\n",
        proposed_content="# new content\ndef foo():\n    return 42\n",
        change_type="modify",
        description="Test change"
    )
    
    verdict = guard.evaluate(request)
    
    print(f"📄 Target: {request.filepath}")
    print(f"🏷️ Category: {verdict.category}")
    print(f"✅ Allowed: {verdict.allowed}")
    print(f"⚠️ Requires Confirmation: {verdict.requires_confirmation}")
    print(f"💡 Recommendation: {verdict.recommendation}")
    print(f"\n📊 Impact:")
    for k, v in verdict.impact_analysis.items():
        print(f"   {k}: {v}")
