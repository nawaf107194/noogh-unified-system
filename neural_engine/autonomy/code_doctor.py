"""
NOOGH Code Doctor
==================
Intelligent code diagnosis using training history.

The system was TRAINED on this codebase. Code Doctor uses that knowledge to:
- Compare current code against learned patterns
- Detect deviations from project style
- Suggest improvements based on project history
- Explain WHY code was written a certain way

Philosophy:
- Training data = historical decisions
- Current code = live implementation
- Difference = opportunity for insight
"""

import os
import re
import ast
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from difflib import SequenceMatcher

from neural_engine.autonomy.file_awareness import (
    FileAwareness, FileCategory, AllowedUse, get_file_awareness
)

logger = logging.getLogger(__name__)


@dataclass
class CodeDiagnosis:
    """Diagnosis result for a file or code snippet."""
    filepath: str
    category: str
    issues: List[Dict]
    suggestions: List[Dict]
    patterns_found: List[str]
    patterns_missing: List[str]
    health_score: float  # 0.0 - 1.0
    summary: str


class CodeDoctor:
    """
    🩺 Code Doctor
    
    Diagnoses code health using project training history.
    """
    
    # Project-specific patterns learned from training
    PROJECT_PATTERNS = {
        "error_handling": {
            "pattern": r"try:\s*\n.*\n\s*except\s+\w+.*:",
            "description": "معالجة الأخطاء بنوع محدد",
            "importance": "high"
        },
        "logging_usage": {
            "pattern": r"logger\.(info|debug|warning|error|critical)\(",
            "description": "استخدام نظام التسجيل",
            "importance": "medium"
        },
        "type_hints": {
            "pattern": r"def \w+\([^)]*:\s*\w+.*\)\s*->",
            "description": "تلميحات الأنواع في الدوال",
            "importance": "medium"
        },
        "docstrings": {
            "pattern": r'"""[^"]+"""',
            "description": "توثيق الكود",
            "importance": "high"
        },
        "dataclass_usage": {
            "pattern": r"@dataclass",
            "description": "استخدام dataclass للبنى",
            "importance": "low"
        },
        "async_patterns": {
            "pattern": r"async def|await ",
            "description": "البرمجة غير المتزامنة",
            "importance": "medium"
        },
        "safety_checks": {
            "pattern": r"if not |if \w+ is None|raise \w+Error",
            "description": "فحوصات السلامة",
            "importance": "high"
        },
        "constants_naming": {
            "pattern": r"^[A-Z][A-Z_0-9]+ = ",
            "description": "تسمية الثوابت بأحرف كبيرة",
            "importance": "low"
        },
    }
    
    # Anti-patterns to detect
    ANTI_PATTERNS = {
        "bare_except": {
            "pattern": r"except:\s*$",
            "description": "except بدون نوع محدد - خطير",
            "severity": "high"
        },
        "magic_numbers": {
            "pattern": r"[^0-9][0-9]{3,}[^0-9]",
            "description": "أرقام سحرية بدون تسمية",
            "severity": "low"
        },
        "todo_fixme": {
            "pattern": r"#\s*(TODO|FIXME|XXX|HACK)",
            "description": "تعليقات TODO/FIXME معلقة",
            "severity": "medium"
        },
        "print_statements": {
            "pattern": r"^\s*print\(",
            "description": "استخدام print بدلاً من logger",
            "severity": "low"
        },
        "hardcoded_paths": {
            "pattern": r'["\'/]home/|["\'/]root/|["\'/]tmp/',
            "description": "مسارات مُثبتة في الكود",
            "severity": "medium"
        },
        "password_in_code": {
            "pattern": r'password\s*=\s*["\'][^"\']+["\']',
            "description": "كلمات مرور مكشوفة",
            "severity": "critical"
        },
    }
    
    def __init__(self):
        self.awareness = get_file_awareness()
        self.base_path = Path("/home/noogh/projects/noogh_unified_system/src")
        logger.info("🩺 Code Doctor initialized")
    
    def diagnose(self, filepath: str) -> CodeDiagnosis:
        """
        Perform a full diagnosis on a file.
        
        Returns:
            CodeDiagnosis with issues, suggestions, and health score
        """
        # Get file context
        ctx = self.awareness.get_file_context(filepath)
        
        # Read file content
        full_path = self._resolve_path(filepath)
        if not full_path.exists():
            return CodeDiagnosis(
                filepath=filepath,
                category=ctx["category"],
                issues=[{"type": "error", "message": "الملف غير موجود"}],
                suggestions=[],
                patterns_found=[],
                patterns_missing=[],
                health_score=0.0,
                summary="❌ الملف غير موجود"
            )
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return CodeDiagnosis(
                filepath=filepath,
                category=ctx["category"],
                issues=[{"type": "error", "message": f"فشل قراءة الملف: {e}"}],
                suggestions=[],
                patterns_found=[],
                patterns_missing=[],
                health_score=0.0,
                summary=f"❌ فشل قراءة الملف"
            )
        
        # Analyze patterns
        patterns_found, patterns_missing = self._check_patterns(content)
        
        # Find anti-patterns
        issues = self._find_anti_patterns(content)
        
        # Generate suggestions based on category
        suggestions = self._generate_suggestions(ctx["category"], patterns_missing, issues)
        
        # Calculate health score
        health_score = self._calculate_health(patterns_found, patterns_missing, issues)
        
        # Generate summary
        summary = self._generate_summary(health_score, issues, ctx["category"])
        
        return CodeDiagnosis(
            filepath=filepath,
            category=ctx["category"],
            issues=issues,
            suggestions=suggestions,
            patterns_found=patterns_found,
            patterns_missing=patterns_missing,
            health_score=health_score,
            summary=summary
        )
    
    def _resolve_path(self, filepath: str) -> Path:
        """Resolve file path."""
        if filepath.startswith('/'):
            return Path(filepath)
        return self.base_path / filepath
    
    def _check_patterns(self, content: str) -> Tuple[List[str], List[str]]:
        """Check which project patterns are present/missing."""
        found = []
        missing = []
        
        for name, info in self.PROJECT_PATTERNS.items():
            if re.search(info["pattern"], content, re.MULTILINE):
                found.append(f"{info['description']}")
            elif info["importance"] in ["high", "medium"]:
                missing.append(f"{info['description']}")
        
        return found, missing
    
    def _find_anti_patterns(self, content: str) -> List[Dict]:
        """Find anti-patterns in the code."""
        issues = []
        
        for name, info in self.ANTI_PATTERNS.items():
            matches = list(re.finditer(info["pattern"], content, re.MULTILINE))
            if matches:
                # Find line numbers
                lines = content[:matches[0].start()].count('\n') + 1
                issues.append({
                    "type": name,
                    "severity": info["severity"],
                    "message": info["description"],
                    "line": lines,
                    "count": len(matches)
                })
        
        return issues
    
    def _generate_suggestions(self, category: str, missing: List[str], issues: List[Dict]) -> List[Dict]:
        """Generate improvement suggestions."""
        suggestions = []
        
        # Based on missing patterns
        for pattern in missing:
            suggestions.append({
                "type": "pattern",
                "priority": "medium",
                "message": f"أضف: {pattern}",
                "reason": "نمط مستخدم في باقي المشروع"
            })
        
        # Based on issues
        for issue in issues:
            if issue["severity"] == "critical":
                suggestions.append({
                    "type": "security",
                    "priority": "critical",
                    "message": f"أصلح فوراً: {issue['message']}",
                    "reason": "مشكلة أمنية"
                })
            elif issue["severity"] == "high":
                suggestions.append({
                    "type": "quality",
                    "priority": "high",
                    "message": f"حسّن: {issue['message']}",
                    "reason": "يؤثر على جودة الكود"
                })
        
        # Category-specific suggestions
        if category == "authority":
            suggestions.append({
                "type": "caution",
                "priority": "info",
                "message": "⚠️ هذا ملف مرجعي - أي تعديل يحتاج مراجعة دقيقة",
                "reason": "ملف أساسي في النظام"
            })
        
        return suggestions
    
    def _calculate_health(self, found: List[str], missing: List[str], issues: List[Dict]) -> float:
        """Calculate overall health score."""
        score = 1.0
        
        # Deduct for missing patterns
        score -= len(missing) * 0.05
        
        # Deduct for issues
        for issue in issues:
            if issue["severity"] == "critical":
                score -= 0.3
            elif issue["severity"] == "high":
                score -= 0.15
            elif issue["severity"] == "medium":
                score -= 0.08
            else:
                score -= 0.03
        
        # Bonus for good patterns
        score += len(found) * 0.02
        
        return max(0.0, min(1.0, score))
    
    def _generate_summary(self, score: float, issues: List[Dict], category: str) -> str:
        """Generate human-readable summary."""
        if score >= 0.9:
            emoji = "🟢"
            status = "ممتاز"
        elif score >= 0.7:
            emoji = "🟡"
            status = "جيد"
        elif score >= 0.5:
            emoji = "🟠"
            status = "يحتاج تحسين"
        else:
            emoji = "🔴"
            status = "يحتاج إصلاح عاجل"
        
        critical = len([i for i in issues if i["severity"] == "critical"])
        high = len([i for i in issues if i["severity"] == "high"])
        
        summary = f"{emoji} {status} ({score:.0%})"
        if critical:
            summary += f" | ⛔ {critical} حرج"
        if high:
            summary += f" | ⚠️ {high} مهم"
        
        return summary
    
    def quick_check(self, filepath: str) -> Dict:
        """Quick health check for API response with actionable insights."""
        diagnosis = self.diagnose(filepath)
        
        # Find top issue (most severe)
        top_issue = None
        if diagnosis.issues:
            # Sort by severity: critical > high > medium > low
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            sorted_issues = sorted(diagnosis.issues, 
                                  key=lambda x: severity_order.get(x.get("severity", "low"), 4))
            top_issue = sorted_issues[0]
        
        # Calculate risk level
        critical_count = len([i for i in diagnosis.issues if i.get("severity") == "critical"])
        high_count = len([i for i in diagnosis.issues if i.get("severity") == "high"])
        
        if critical_count > 0:
            risk_level = "critical"
            risk_label = "⛔ حرج"
        elif high_count > 0:
            risk_level = "high"
            risk_label = "🔴 عالي"
        elif len(diagnosis.issues) > 3:
            risk_level = "medium"
            risk_label = "🟡 متوسط"
        else:
            risk_level = "low"
            risk_label = "🟢 منخفض"
        
        # Identify areas of concern
        areas = []
        area_mapping = {
            "password_in_code": "security",
            "bare_except": "quality",
            "hardcoded_paths": "maintainability",
            "todo_fixme": "completeness",
            "print_statements": "production",
            "magic_numbers": "readability",
        }
        for issue in diagnosis.issues:
            area = area_mapping.get(issue.get("type"), "general")
            if area not in areas:
                areas.append(area)
        
        return {
            "filepath": filepath,
            "category": diagnosis.category,
            "health_score": diagnosis.health_score,
            "health_label": self._health_label(diagnosis.health_score),
            "summary": diagnosis.summary,
            
            # NEW: Actionable insights
            "risk_level": risk_level,
            "risk_label": risk_label,
            "top_issue": {
                "type": top_issue.get("type"),
                "severity": top_issue.get("severity"),
                "message": top_issue.get("message"),
                "line": top_issue.get("line"),
            } if top_issue else None,
            "areas": areas,
            
            # Counts
            "issues_count": len(diagnosis.issues),
            "critical_issues": critical_count,
            "high_issues": high_count,
            "suggestions_count": len(diagnosis.suggestions),
            "patterns_found": len(diagnosis.patterns_found),
            "patterns_missing": len(diagnosis.patterns_missing)
        }
    
    def full_diagnosis(self, filepath: str) -> Dict:
        """Full diagnosis for API response."""
        diagnosis = self.diagnose(filepath)
        
        return {
            "filepath": filepath,
            "category": diagnosis.category,
            "health_score": diagnosis.health_score,
            "health_label": self._health_label(diagnosis.health_score),
            "summary": diagnosis.summary,
            "issues": diagnosis.issues,
            "suggestions": diagnosis.suggestions,
            "patterns_found": diagnosis.patterns_found,
            "patterns_missing": diagnosis.patterns_missing,
            "guidance": self.awareness._get_guidance(FileCategory(diagnosis.category))
        }
    
    def _health_label(self, score: float) -> str:
        """Get health label."""
        if score >= 0.9:
            return "🟢 ممتاز"
        elif score >= 0.7:
            return "🟡 جيد"
        elif score >= 0.5:
            return "🟠 متوسط"
        else:
            return "🔴 يحتاج إصلاح"
    
    def compare_with_pattern(self, filepath: str, pattern_file: str) -> Dict:
        """
        Compare a file against a pattern file from the project.
        
        This uses the training knowledge to identify deviations.
        """
        # Get both files
        target_path = self._resolve_path(filepath)
        pattern_path = self._resolve_path(pattern_file)
        
        if not target_path.exists() or not pattern_path.exists():
            return {"error": "أحد الملفات غير موجود"}
        
        with open(target_path, 'r') as f:
            target_content = f.read()
        with open(pattern_path, 'r') as f:
            pattern_content = f.read()
        
        # Compare structure using AST
        try:
            target_tree = ast.parse(target_content)
            pattern_tree = ast.parse(pattern_content)
            
            target_funcs = [n.name for n in ast.walk(target_tree) if isinstance(n, ast.FunctionDef)]
            pattern_funcs = [n.name for n in ast.walk(pattern_tree) if isinstance(n, ast.FunctionDef)]
            
            # Find pattern functions not in target
            missing_patterns = [f for f in pattern_funcs if f not in target_funcs and not f.startswith('_')]
            
        except SyntaxError:
            missing_patterns = []
        
        # Calculate similarity
        similarity = SequenceMatcher(None, target_content, pattern_content).ratio()
        
        return {
            "target": filepath,
            "pattern": pattern_file,
            "similarity": round(similarity, 2),
            "missing_patterns": missing_patterns,
            "recommendation": self._get_comparison_recommendation(similarity, missing_patterns)
        }
    
    def _get_comparison_recommendation(self, similarity: float, missing: List[str]) -> str:
        """Get recommendation based on comparison."""
        if similarity > 0.8:
            return "✅ متوافق مع النمط"
        elif similarity > 0.5:
            if missing:
                return f"🟡 قريب من النمط، لكن ينقصه: {', '.join(missing[:3])}"
            return "🟡 بنية مختلفة قليلاً"
        else:
            return "⚠️ مختلف كثيراً عن النمط المرجعي"


# ========== Singleton ==========

_code_doctor: Optional[CodeDoctor] = None

def get_code_doctor() -> CodeDoctor:
    """Get the global code doctor instance."""
    global _code_doctor
    if _code_doctor is None:
        _code_doctor = CodeDoctor()
    return _code_doctor


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    doctor = CodeDoctor()
    
    # Test diagnosis
    print("🩺 Code Doctor Test\n")
    
    test_files = [
        "neural_engine/reasoning/react_loop.py",
        "neural_engine/autonomy/constitution.py",
    ]
    
    for f in test_files:
        result = doctor.quick_check(f)
        print(f"📄 {f}")
        print(f"   {result['summary']}")
        print(f"   Issues: {result['issues_count']}, Suggestions: {result['suggestions_count']}")
        print()
