"""
NOOGH Intent Registry
======================
Structured catalog of what the system can understand and do.

Intent = What the user wants
Action = What the system does

This provides:
1. Structured understanding of user requests
2. Mapping intents to actions
3. Parameter extraction
4. Confidence scoring
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Pattern
from enum import Enum

logger = logging.getLogger(__name__)


class IntentCategory(Enum):
    """Categories of user intents."""
    GREETING = "greeting"
    IDENTITY = "identity"
    SYSTEM_MONITOR = "system_monitor"
    CODE_ANALYSIS = "code_analysis"
    FILE_OPERATION = "file_operation"
    KNOWLEDGE = "knowledge"
    CREATIVE = "creative"
    DEVELOPMENT = "development"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Represents a registered intent."""
    id: str
    name: str
    category: IntentCategory
    patterns: List[str]  # Regex patterns
    action: str  # Action path key
    description: str
    parameters: List[str] = field(default_factory=list)  # Expected parameters
    requires_confirmation: bool = False
    enabled: bool = True
    examples: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # Compile patterns
        self._compiled_patterns: List[Pattern] = [
            re.compile(p, re.IGNORECASE | re.UNICODE) 
            for p in self.patterns
        ]


@dataclass 
class IntentMatch:
    """Result of intent matching."""
    intent: Intent
    confidence: float  # 0.0 to 1.0
    matched_pattern: str
    extracted_params: Dict[str, str] = field(default_factory=dict)


class IntentRegistry:
    """
    📋 Intent Registry
    
    Central catalog of all understood intents.
    Provides intent detection and parameter extraction.
    """
    
    def __init__(self):
        self.intents: Dict[str, Intent] = {}
        self._register_default_intents()
        logger.info(f"📋 Intent Registry initialized with {len(self.intents)} intents")
    
    def _register_default_intents(self):
        """Register default intents."""
        
        # === GREETING ===
        self.register(Intent(
            id="greet",
            name="Greeting",
            category=IntentCategory.GREETING,
            patterns=[
                r"^(مرحبا|السلام|اهلا|هاي|صباح|مساء|hello|hi|hey)\b",
            ],
            action="direct_response",
            description="User greeting",
            examples=["مرحبا نوقه", "السلام عليكم", "Hi"]
        ))
        
        # === IDENTITY ===
        self.register(Intent(
            id="who_are_you",
            name="Identity Question",
            category=IntentCategory.IDENTITY,
            patterns=[
                r"(من أنت|مين انت|تعرف نفسك|who are you|what are you)",
                r"(اسمك|your name)",
            ],
            action="direct_response",
            description="Identity question",
            examples=["من أنت؟", "ما اسمك؟"]
        ))
        
        # === SYSTEM MONITORING ===
        self.register(Intent(
            id="check_memory",
            name="Check Memory",
            category=IntentCategory.SYSTEM_MONITOR,
            patterns=[
                r"(ذاكرة|memory|ram|الرام)",
                r"(استهلاك|استخدام).*(ذاكرة|memory)",
            ],
            action="shell:free -h",
            description="Check memory usage",
            examples=["كم استهلاك الذاكرة؟", "memory usage"]
        ))
        
        self.register(Intent(
            id="check_disk",
            name="Check Disk",
            category=IntentCategory.SYSTEM_MONITOR,
            patterns=[
                r"(مساحة|disk|storage|قرص|تخزين)",
            ],
            action="shell:df -h --total | grep -E '(Filesystem|total|/$)'",
            description="Check disk space",
            examples=["كم المساحة المتبقية؟", "disk space"]
        ))
        
        self.register(Intent(
            id="check_processes",
            name="Check Processes",
            category=IntentCategory.SYSTEM_MONITOR,
            patterns=[
                r"(عمليات|processes|العمليات|البرامج)",
                r"(أعلى|top|الأكثر).*(استهلاك)",
            ],
            action="shell:ps aux --sort=-%cpu | head -8",
            description="Check top processes",
            examples=["ما هي أعلى العمليات؟", "top processes"]
        ))
        
        self.register(Intent(
            id="check_time",
            name="Check Time",
            category=IntentCategory.SYSTEM_MONITOR,
            patterns=[
                r"(الوقت|الساعة|time|date|التاريخ)",
            ],
            action="shell:date '+%A %d %B %Y - %H:%M:%S'",
            description="Check date and time",
            examples=["كم الساعة؟", "what time is it?"]
        ))
        
        # === CODE ANALYSIS ===
        self.register(Intent(
            id="read_file",
            name="Read File",
            category=IntentCategory.FILE_OPERATION,
            patterns=[
                r"(اقرأ|اعرض|افتح|read|show|cat).*(ملف|file)\s+(\S+\.py)",
            ],
            action="read_file",
            description="Read a file",
            parameters=["filename"],
            examples=["اقرأ ملف main.py", "show file config.py"]
        ))
        
        self.register(Intent(
            id="search_code",
            name="Search Code",
            category=IntentCategory.CODE_ANALYSIS,
            patterns=[
                r"(ابحث|search|grep|find).*(عن|for)?\s+(.+)",
            ],
            action="code_search",
            description="Search in codebase",
            parameters=["query"],
            examples=["ابحث عن ReActResult", "search for def main"]
        ))
        
        self.register(Intent(
            id="project_structure",
            name="Project Structure",
            category=IntentCategory.CODE_ANALYSIS,
            patterns=[
                r"(بنية|هيكل|structure|tree).*(المشروع|project)?",
            ],
            action="shell:find /home/noogh/projects/noogh_unified_system/src -type d -name 'neural_engine' -o -name 'training_data' | head -10",
            description="Show project structure",
            examples=["اعرض بنية المشروع", "project structure"]
        ))
        
        # === DEVELOPMENT ===
        self.register(Intent(
            id="run_tests",
            name="Run Tests",
            category=IntentCategory.DEVELOPMENT,
            patterns=[
                r"(الاختبارات|tests|pytest|شغل.*اختبار)",
            ],
            action="shell:cd /home/noogh/projects/noogh_unified_system && python -m pytest src/ -v --tb=short 2>&1 | head -30",
            description="Run project tests",
            requires_confirmation=False,
            examples=["شغل الاختبارات", "run pytest"]
        ))
        
        self.register(Intent(
            id="git_status",
            name="Git Status",
            category=IntentCategory.DEVELOPMENT,
            patterns=[
                r"(git\s+status|حالة\s+git|الملفات\s+المعدلة)",
            ],
            action="shell:cd /home/noogh/projects/noogh_unified_system && git status --short | head -15",
            description="Show git status",
            examples=["git status", "حالة git"]
        ))
        
        # === KNOWLEDGE ===
        self.register(Intent(
            id="explain",
            name="Explain/Teach",
            category=IntentCategory.KNOWLEDGE,
            patterns=[
                r"(اشرح|علمني|ما هو|ما هي|explain|what is|how to)",
            ],
            action="knowledge_path",
            description="Educational question",
            examples=["اشرح machine learning", "ما هو API؟"]
        ))
        
        # === CREATIVE ===
        self.register(Intent(
            id="creative_request",
            name="Creative Request",
            category=IntentCategory.CREATIVE,
            patterns=[
                r"(اكتب|ألف|أنشئ|create|write).*(قصة|شعر|كود|story|poem|code)",
            ],
            action="llm_required",
            description="Creative writing request",
            examples=["اكتب قصة قصيرة", "write a poem"]
        ))
        
        # === HELP ===
        self.register(Intent(
            id="help",
            name="Help",
            category=IntentCategory.HELP,
            patterns=[
                r"(مساعدة|help|أوامر|commands|ماذا تستطيع)",
            ],
            action="show_help",
            description="Show help",
            examples=["مساعدة", "help", "ماذا تستطيع؟"]
        ))
    
    def register(self, intent: Intent):
        """Register an intent."""
        self.intents[intent.id] = intent
    
    def match(self, query: str) -> Optional[IntentMatch]:
        """Match query against registered intents."""
        best_match: Optional[IntentMatch] = None
        best_confidence = 0.0
        
        query_lower = query.lower()
        
        for intent in self.intents.values():
            if not intent.enabled:
                continue
            
            for pattern in intent._compiled_patterns:
                match = pattern.search(query_lower)
                if match:
                    # Calculate confidence based on match quality
                    match_length = len(match.group())
                    query_length = len(query)
                    confidence = min(0.5 + (match_length / query_length) * 0.5, 1.0)
                    
                    if confidence > best_confidence:
                        # Extract parameters from groups
                        params = {}
                        if match.groups():
                            for i, group in enumerate(match.groups()):
                                if group and i < len(intent.parameters):
                                    params[intent.parameters[i]] = group
                        
                        best_match = IntentMatch(
                            intent=intent,
                            confidence=confidence,
                            matched_pattern=pattern.pattern,
                            extracted_params=params
                        )
                        best_confidence = confidence
        
        return best_match
    
    def get_by_category(self, category: IntentCategory) -> List[Intent]:
        """Get all intents in a category."""
        return [i for i in self.intents.values() if i.category == category]
    
    def get_help_text(self) -> str:
        """Generate help text for all intents."""
        help_text = "🤖 **قدرات نوقه:**\n\n"
        
        for category in IntentCategory:
            intents = self.get_by_category(category)
            if not intents:
                continue
            
            help_text += f"**{category.value.replace('_', ' ').title()}:**\n"
            for intent in intents:
                examples = ", ".join(intent.examples[:2]) if intent.examples else ""
                help_text += f"  • {intent.name}: {intent.description}\n"
                if examples:
                    help_text += f"    مثال: {examples}\n"
            help_text += "\n"
        
        return help_text


# ========== Singleton ==========

_registry: Optional[IntentRegistry] = None

def get_intent_registry() -> IntentRegistry:
    """Get or create global intent registry."""
    global _registry
    if _registry is None:
        _registry = IntentRegistry()
    return _registry


if __name__ == "__main__":
    # Test intent matching
    registry = IntentRegistry()
    
    test_queries = [
        "مرحبا نوقه",
        "كم استهلاك الذاكرة؟",
        "ابحث عن ReActResult",
        "اقرأ ملف main.py",
        "git status",
        "مساعدة",
    ]
    
    for query in test_queries:
        match = registry.match(query)
        if match:
            print(f"'{query}' → {match.intent.name} (conf: {match.confidence:.2f})")
        else:
            print(f"'{query}' → No match")
