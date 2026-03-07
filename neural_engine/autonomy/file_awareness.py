"""
NOOGH File Awareness Layer
===========================
Intelligent file classification and usage policy.

The system was TRAINED on its own codebase. This layer ensures
the training is used WISELY - not blindly.

File Categories:
- 🟢 AUTHORITY: Core files - reference only, no auto-modify
- 🔵 PATTERN: Templates/examples - use for generation
- 🔴 HISTORICAL: Old/experimental - understand only
- 🟣 SENSITIVE: Security files - explicit request only

Philosophy:
- Training = raw memory
- File Awareness = operational consciousness
- Combined = Sovereign Agent
"""

import os
import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class FileCategory(Enum):
    """File classification categories."""
    AUTHORITY = "authority"      # Core logic - reference only
    PATTERN = "pattern"          # Templates - use for generation
    HISTORICAL = "historical"    # Old/experimental - understand only
    SENSITIVE = "sensitive"      # Security - explicit request only
    GENERATED = "generated"      # Auto-generated - can modify
    DATA = "data"               # Training/config data
    UNKNOWN = "unknown"         # Unclassified


class AllowedUse(Enum):
    """What the system is allowed to do with a file."""
    EXPLAIN = "explain"          # Can explain what it does
    ANALYZE = "analyze"          # Can analyze for issues
    REFERENCE = "reference"      # Can use as reference
    GENERATE_FROM = "generate"   # Can use as template
    MODIFY_SUGGEST = "suggest"   # Can suggest modifications
    AUTO_MODIFY = "auto_modify"  # Can modify automatically
    EXECUTE = "execute"          # Can execute/run


@dataclass
class FilePolicy:
    """Policy for a specific file or pattern."""
    category: FileCategory
    allowed: Set[AllowedUse]
    forbidden: Set[AllowedUse]
    requires_confirmation: bool = False
    description: str = ""


class FileAwareness:
    """
    🧠 File Awareness Layer
    
    Maps files to categories and usage policies.
    Ensures training data is used with CONTEXT and PURPOSE.
    """
    
    # Authority files - CORE LOGIC (expanded)
    AUTHORITY_PATTERNS = [
        # Core files by name
        r"react_loop\.py$",
        r"decision_engine\.py$",
        r"safety_policy\.py$",
        r"constitution\.py$",
        r"file_awareness\.py$",
        r"file_classifier\.py$",
        r"code_doctor\.py$",
        r"change_guard\.py$",
        r"intent_registry\.py$",
        r"monitor\.py$",
        r"self_learner\.py$",
        r"reasoning_engine\.py$",
        r"tool_executor\.py$",
        r"routes\.py$",
        r"main\.py$",
        r"__init__\.py$",
        r"noogh_core\.py$",
        r"agent_daemon\.py$",
        r"orchestrator\.py$",
        # Core directories
        r"reasoning/.*\.py$",
        r"autonomy/.*\.py$",
        r"core/.*\.py$",
        r"api/.*\.py$",
        r"engine/.*\.py$",
        # Gateway and server files
        r"gateway/.*\.py$",
        r"mcp_server/.*\.py$",
        # Agent files
        r"agents?/.*\.py$",
        # Service files
        r".*_service/.*\.py$",
        r"sandbox_service/.*\.py$",
        # Observability and ops
        r"observability_suite/.*\.py$",
        r"neural_api_debug/.*\.py$",
        r"ops/.*\.py$",
        # Shared modules
        r"shared/.*\.py$",
        # Config files (Python)
        r"config/.*\.py$",
        # Root level NOOGH files
        r"^noogh_.*\.py$",
        r"^tools_.*\.py$",
        r"^forensics_.*\.py$",
    ]
    
    # Pattern files - TEMPLATES (expanded)
    PATTERN_PATTERNS = [
        # Utility directories
        r"handlers/.*\.py$",
        r"utils/.*\.py$",
        r"helpers/.*\.py$",
        r"scripts/.*\.(py|sh)$",
        r"executors/.*\.py$",
        r"processors/.*\.py$",
        r"playbooks/.*$",
        r"templates/.*$",
        r"tools/.*\.py$",
        r"cli/.*\.py$",
        r"bridges/.*\.py$",
        r"adapters/.*\.py$",
        r"formatters/.*\.py$",
        r"plugins/.*\.py$",
        # Executable scripts by name pattern
        r"run_.*\.py$",
        r"start_.*\.py$",
        r"exec_.*\.py$",
        r"launch_.*\.py$",
        r"train_.*\.py$",  # Training scripts are PATTERN not DATA
        r"deploy_.*\.py$",
        r"setup_.*\.py$",
        r"install_.*\.py$",
        r"check_.*\.py$",
        r"validate_.*\.py$",
        r"build_.*\.py$",
        r"generate_.*\.py$",
        r"migrate_.*\.py$",
        # Demo and example files
        r"demo/.*\.py$",
        r"examples?/.*\.py$",
    ]
    
    # Historical files - OLD/EXPERIMENTAL (expanded)
    HISTORICAL_PATTERNS = [
        r"old_.*\.py$",
        r".*_old\.py$",
        r".*_backup\.py$",
        r".*_v[0-9]+\.py$",
        r"legacy/.*$",
        r"experiments?/.*$",
        r"test_.*\.py$",
        r".*_test\.py$",
        r"tests/.*\.py$",
        r"deprecated/.*$",
        r"archive/.*$",
        r"drafts?/.*$",
        r"poc/.*$",
        r"prototype/.*$",
        r"bak/.*$",
        # Compiled/cache directories
        r"unsloth_compiled_cache/.*$",
        r".*_cache/.*$",
        # Dataset generation (historical)
        r"sovereign_dataset.*/.*\.py$",
        r"agent_dataset_generator/.*\.py$",
        # Training related historical
        r"training/Unsloth.*\.py$",
    ]
    
    # Sensitive files - SECURITY (expanded)
    SENSITIVE_PATTERNS = [
        r"auth.*\.py$",
        r".*_auth\.py$",
        r"security.*\.py$",
        r".*password.*$",
        r".*secret.*$",
        r".*token.*$",
        r".*_key\.py$",
        r".*key_.*\.py$",
        r"\.env$",
        r"config/.*\.(yaml|yml|json)$",
        r"credentials.*$",
        r"oauth.*\.py$",
        r"jwt.*\.py$",
        r"encrypt.*\.py$",
        r"decrypt.*\.py$",
        r"hash.*\.py$",
        r"sign.*\.py$",
        r"verify.*\.py$",
    ]
    
    # Generated files - CAN MODIFY
    GENERATED_PATTERNS = [
        r".*\.log$",
        r".*\.cache$",
        r"__pycache__/.*$",
        r"\.git/.*$",
        r".*\.pyc$",
        r"generated/.*$",
        r"build/.*$",
        r"dist/.*$",
        r"\.eggs/.*$",
        r".*\.egg-info/.*$",
    ]
    
    # Data files (non-Python)
    DATA_PATTERNS = [
        r".*\.jsonl$",
        r".*\.json$",
        r"training_data/.*$",
        r"datasets?/.*$",
        r".*\.yaml$",
        r".*\.yml$",
        r".*\.csv$",
        r".*\.parquet$",
        r"data/.*$",
        r"fixtures/.*$",
        r"samples/.*$",
    ]
    
    def __init__(self):
        self.base_path = Path("/home/noogh/projects/noogh_unified_system/src")
        self.file_cache: Dict[str, FilePolicy] = {}
        self._build_category_patterns()
        logger.info("🧠 File Awareness Layer initialized")
    
    def _build_category_patterns(self):
        """Compile regex patterns for efficiency."""
        self.compiled_patterns = {
            FileCategory.AUTHORITY: [re.compile(p) for p in self.AUTHORITY_PATTERNS],
            FileCategory.PATTERN: [re.compile(p) for p in self.PATTERN_PATTERNS],
            FileCategory.HISTORICAL: [re.compile(p) for p in self.HISTORICAL_PATTERNS],
            FileCategory.SENSITIVE: [re.compile(p) for p in self.SENSITIVE_PATTERNS],
            FileCategory.GENERATED: [re.compile(p) for p in self.GENERATED_PATTERNS],
            FileCategory.DATA: [re.compile(p) for p in self.DATA_PATTERNS],
        }
    
    def classify(self, filepath: str) -> FileCategory:
        """Classify a file into a category."""
        # Normalize path
        if not filepath.startswith('/'):
            filepath = str(self.base_path / filepath)
        
        rel_path = filepath
        if filepath.startswith(str(self.base_path)):
            rel_path = filepath[len(str(self.base_path))+1:]
        
        # Check each category in priority order
        priority_order = [
            FileCategory.SENSITIVE,    # Check sensitive FIRST
            FileCategory.AUTHORITY,
            FileCategory.PATTERN,
            FileCategory.HISTORICAL,
            FileCategory.GENERATED,
            FileCategory.DATA,
        ]
        
        for category in priority_order:
            for pattern in self.compiled_patterns[category]:
                if pattern.search(rel_path) or pattern.search(os.path.basename(filepath)):
                    return category
        
        return FileCategory.UNKNOWN
    
    def get_policy(self, filepath: str) -> FilePolicy:
        """Get the usage policy for a file."""
        # Check cache
        if filepath in self.file_cache:
            return self.file_cache[filepath]
        
        category = self.classify(filepath)
        
        # Define policies per category
        policies = {
            FileCategory.AUTHORITY: FilePolicy(
                category=FileCategory.AUTHORITY,
                allowed={AllowedUse.EXPLAIN, AllowedUse.ANALYZE, AllowedUse.REFERENCE},
                forbidden={AllowedUse.AUTO_MODIFY, AllowedUse.EXECUTE},
                requires_confirmation=True,
                description="ملف مرجعي - للقراءة والتحليل فقط"
            ),
            FileCategory.PATTERN: FilePolicy(
                category=FileCategory.PATTERN,
                allowed={AllowedUse.EXPLAIN, AllowedUse.ANALYZE, AllowedUse.REFERENCE, 
                        AllowedUse.GENERATE_FROM, AllowedUse.MODIFY_SUGGEST},
                forbidden={AllowedUse.AUTO_MODIFY},
                requires_confirmation=False,
                description="ملف نمطي - يمكن استخدامه كقالب"
            ),
            FileCategory.HISTORICAL: FilePolicy(
                category=FileCategory.HISTORICAL,
                allowed={AllowedUse.EXPLAIN, AllowedUse.REFERENCE},
                forbidden={AllowedUse.AUTO_MODIFY, AllowedUse.GENERATE_FROM, AllowedUse.EXECUTE},
                requires_confirmation=False,
                description="ملف تاريخي - للفهم فقط"
            ),
            FileCategory.SENSITIVE: FilePolicy(
                category=FileCategory.SENSITIVE,
                allowed={AllowedUse.EXPLAIN},
                forbidden={AllowedUse.AUTO_MODIFY, AllowedUse.EXECUTE, AllowedUse.GENERATE_FROM},
                requires_confirmation=True,
                description="ملف حساس - يحتاج طلب صريح"
            ),
            FileCategory.GENERATED: FilePolicy(
                category=FileCategory.GENERATED,
                allowed={AllowedUse.EXPLAIN, AllowedUse.ANALYZE, AllowedUse.AUTO_MODIFY},
                forbidden=set(),
                requires_confirmation=False,
                description="ملف مُولَّد - يمكن التعديل"
            ),
            FileCategory.DATA: FilePolicy(
                category=FileCategory.DATA,
                allowed={AllowedUse.EXPLAIN, AllowedUse.ANALYZE, AllowedUse.REFERENCE},
                forbidden={AllowedUse.AUTO_MODIFY, AllowedUse.EXECUTE},
                requires_confirmation=False,
                description="ملف بيانات - للقراءة"
            ),
            FileCategory.UNKNOWN: FilePolicy(
                category=FileCategory.UNKNOWN,
                allowed={AllowedUse.EXPLAIN, AllowedUse.ANALYZE},
                forbidden={AllowedUse.AUTO_MODIFY, AllowedUse.EXECUTE},
                requires_confirmation=True,
                description="ملف غير مصنف - احتياط"
            ),
        }
        
        policy = policies.get(category, policies[FileCategory.UNKNOWN])
        self.file_cache[filepath] = policy
        return policy
    
    def can_use(self, filepath: str, use: AllowedUse) -> Tuple[bool, str]:
        """
        Check if a specific use is allowed for a file.
        
        Returns:
            (allowed: bool, reason: str)
        """
        policy = self.get_policy(filepath)
        
        if use in policy.forbidden:
            return False, f"⛔ الاستخدام '{use.value}' ممنوع لهذا الملف ({policy.category.value})"
        
        if use in policy.allowed:
            if policy.requires_confirmation:
                return True, f"⚠️ مسموح مع تأكيد ({policy.description})"
            return True, f"✅ مسموح ({policy.description})"
        
        return False, f"❓ الاستخدام '{use.value}' غير محدد لهذا الملف"
    
    def check_modification(self, filepath: str, auto: bool = False) -> Dict:
        """
        Check if file modification is allowed.
        
        Args:
            filepath: Path to file
            auto: Whether this is an automatic modification
            
        Returns:
            {allowed, requires_confirmation, reason, category}
        """
        policy = self.get_policy(filepath)
        use = AllowedUse.AUTO_MODIFY if auto else AllowedUse.MODIFY_SUGGEST
        
        allowed, reason = self.can_use(filepath, use)
        
        return {
            "allowed": allowed,
            "requires_confirmation": policy.requires_confirmation,
            "reason": reason,
            "category": policy.category.value,
            "description": policy.description
        }
    
    def get_file_context(self, filepath: str) -> Dict:
        """
        Get full context about how to use a file.
        Used when the model needs to interact with a file.
        """
        policy = self.get_policy(filepath)
        
        # Build usage guide
        allowed_list = [u.value for u in policy.allowed]
        forbidden_list = [u.value for u in policy.forbidden]
        
        context = {
            "filepath": filepath,
            "category": policy.category.value,
            "description": policy.description,
            "allowed_uses": allowed_list,
            "forbidden_uses": forbidden_list,
            "requires_confirmation": policy.requires_confirmation,
            "guidance": self._get_guidance(policy.category)
        }
        
        return context
    
    def _get_guidance(self, category: FileCategory) -> str:
        """Get specific guidance for interacting with a file category."""
        guidance = {
            FileCategory.AUTHORITY: """
🟢 **ملف مرجعي (Authority)**
- ✅ اشرح كيف يعمل
- ✅ حلل المشاكل
- ✅ استخدمه كمرجع
- ❌ لا تعدله تلقائياً
- ❌ لا تقترح تغييرات جذرية
- ⚠️ أي تعديل يحتاج diff + شرح + تأكيد
""",
            FileCategory.PATTERN: """
🔵 **ملف نمطي (Pattern)**
- ✅ استخدمه كقالب لتوليد كود جديد
- ✅ اقترح تحسينات
- ✅ انسخ الأسلوب والبنية
- ❌ لا تعدل الأصل تلقائياً
""",
            FileCategory.HISTORICAL: """
🔴 **ملف تاريخي (Historical)**
- ✅ اقرأ لفهم القرارات السابقة
- ❌ لا تستخدمه كمرجع للكود الجديد
- ❌ لا تقترحه كحل افتراضي
- ⚠️ قد يحتوي على أساليب قديمة
""",
            FileCategory.SENSITIVE: """
🟣 **ملف حساس (Sensitive)**
- ⚠️ يحتاج طلب صريح للوصول
- ❌ لا تعرض محتواه كاملاً
- ❌ لا تستخدمه في الأمثلة
- 🔒 تحت Safety Policy مشددة
""",
            FileCategory.GENERATED: """
⚪ **ملف مُولَّد (Generated)**
- ✅ يمكن حذفه أو تعديله
- ✅ لا قيمة تاريخية له
- ⚠️ قد يُعاد توليده
""",
            FileCategory.DATA: """
📊 **ملف بيانات (Data)**
- ✅ اقرأ واستخدم كمرجع
- ❌ لا تعدل بدون سبب واضح
- ⚠️ قد يكون مصدر التدريب
""",
        }
        return guidance.get(category, "❓ ملف غير مصنف - تعامل بحذر")
    
    def summarize_project(self) -> Dict:
        """Generate a summary of project file categories."""
        summary = {cat.value: [] for cat in FileCategory}
        
        for root, dirs, files in os.walk(self.base_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for f in files:
                if f.endswith('.py'):
                    filepath = os.path.join(root, f)
                    rel_path = os.path.relpath(filepath, self.base_path)
                    category = self.classify(filepath)
                    summary[category.value].append(rel_path)
        
        return summary


# ========== Singleton ==========

_file_awareness: Optional[FileAwareness] = None

def get_file_awareness() -> FileAwareness:
    """Get the global file awareness instance."""
    global _file_awareness
    if _file_awareness is None:
        _file_awareness = FileAwareness()
    return _file_awareness


def check_file_use(filepath: str, use: str) -> Tuple[bool, str]:
    """Quick check if file use is allowed."""
    try:
        use_enum = AllowedUse(use)
    except ValueError:
        return False, f"Unknown use type: {use}"
    return get_file_awareness().can_use(filepath, use_enum)


def get_file_category(filepath: str) -> str:
    """Get the category of a file."""
    return get_file_awareness().classify(filepath).value


if __name__ == "__main__":
    # Test the file awareness
    logging.basicConfig(level=logging.INFO)
    
    awareness = FileAwareness()
    
    test_files = [
        "neural_engine/reasoning/react_loop.py",
        "neural_engine/autonomy/safety_policy.py",
        "neural_engine/utils/helpers.py",
        "scripts/deploy.sh",
        "old_implementation.py",
        "neural_engine/api/security.py",
        "training_data/samples.jsonl",
    ]
    
    print("🧠 File Awareness Test:\n")
    for f in test_files:
        ctx = awareness.get_file_context(f)
        print(f"📄 {f}")
        print(f"   Category: {ctx['category']}")
        print(f"   {ctx['description']}")
        print(f"   Allowed: {', '.join(ctx['allowed_uses'])}")
        print(f"   Forbidden: {', '.join(ctx['forbidden_uses'])}")
        print()
