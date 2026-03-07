"""
🧠 NOOGH Tier-10A — Meta-Intent Expansion Engine
=================================================
Expands composite natural language requests into structured multi-tool plans.

Philosophy:
- "health check شامل" → [cpu, memory, disk, processes, network]
- Without execution, without assumptions
- Deterministic, auditable expansion

This is the DEPTH layer that transforms:
  "أعطني تقرير شامل عن النظام"
Into:
  [
    {"subsystem": "cpu", "tool": "top", "args": "-bn1"},
    {"subsystem": "memory", "tool": "free", "args": "-h"},
    {"subsystem": "disk", "tool": "df", "args": "-h"},
    {"subsystem": "processes", "tool": "ps", "args": "aux --sort=-%mem"},
    {"subsystem": "network", "tool": "ip", "args": "addr"},
  ]
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import re


@dataclass
class IntentComponent:
    """A single component of a composite intent."""
    subsystem: str
    tool: str
    args: str
    description: str
    priority: int = 1
    optional: bool = False


@dataclass  
class ExpandedIntent:
    """Result of intent expansion."""
    original_query: str
    detected_meta_intent: Optional[str]
    components: List[IntentComponent]
    expansion_confidence: float
    requires_all: bool  # True = AND, False = OR
    estimated_complexity: str  # "simple", "moderate", "complex"
    warnings: List[str] = field(default_factory=list)


class MetaIntentExpander:
    """
    Expands composite natural language intents into structured plans.
    
    This is NOT an LLM — it's a deterministic pattern matcher
    that recognizes meta-intent patterns and expands them.
    """
    
    # ==================== Meta-Intent Patterns ====================
    
    # Comprehensive/Full patterns
    COMPREHENSIVE_PATTERNS = [
        r"شامل",
        r"كامل",
        r"comprehensive",
        r"full",
        r"complete",
        r"all",
        r"everything",
        r"كل شي",
        r"جميع",
    ]
    
    # Health check patterns
    HEALTH_PATTERNS = [
        r"health\s*check",
        r"فحص\s*صحة",
        r"حالة\s*النظام",
        r"system\s*status",
        r"تشخيص",
        r"diagnos",
        r"تقرير",
        r"report",
    ]
    
    # Analysis patterns
    ANALYSIS_PATTERNS = [
        r"حلل",
        r"analyz",
        r"check",
        r"فحص",
        r"راقب",
        r"monitor",
        r"inspect",
    ]
    
    # ==================== Subsystem Definitions ====================
    
    SUBSYSTEMS = {
        "cpu": {
            "keywords": [r"cpu", r"معالج", r"processor", r"load", r"حمل"],
            "tools": [
                IntentComponent("cpu", "top", "-bn1 | head -20", "CPU and top processes", 1),
                IntentComponent("cpu", "uptime", "", "System load averages", 2),
            ],
            "description": "المعالج/CPU"
        },
        "memory": {
            "keywords": [r"ram", r"memory", r"mem", r"ذاكرة", r"الذاكرة"],
            "tools": [
                IntentComponent("memory", "free", "-h", "Memory usage", 1),
            ],
            "description": "الذاكرة/RAM"
        },
        "disk": {
            "keywords": [r"disk", r"قرص", r"مساحة", r"storage", r"تخزين", r"hdd", r"ssd"],
            "tools": [
                IntentComponent("disk", "df", "-h", "Disk space usage", 1),
                IntentComponent("disk", "du", "-sh /var/log 2>/dev/null", "Log directory size", 2, True),
            ],
            "description": "القرص/Disk"
        },
        "processes": {
            "keywords": [r"process", r"عمليات", r"عملية", r"برامج", r"تطبيقات"],
            "tools": [
                IntentComponent("processes", "ps", "aux --sort=-%mem | head -15", "Top processes", 1),
            ],
            "description": "العمليات/Processes"
        },
        "network": {
            "keywords": [r"network", r"شبكة", r"net", r"اتصال", r"انترنت", r"ip"],
            "tools": [
                IntentComponent("network", "ip", "addr | grep -E 'inet |state'", "Network interfaces", 1),
                IntentComponent("network", "ss", "-tuln | head -10", "Listening ports", 2, True),
            ],
            "description": "الشبكة/Network"
        },
        "services": {
            "keywords": [r"service", r"خدمات", r"daemon", r"systemd"],
            "tools": [
                IntentComponent("services", "systemctl", "list-units --state=failed", "Failed services", 1),
            ],
            "description": "الخدمات/Services"
        },
    }
    
    # ==================== Core Logic ====================
    
    @classmethod
    def expand(cls, query: str) -> ExpandedIntent:
        """
        Expand a natural language query into structured intent components.
        
        Returns:
            ExpandedIntent with components, confidence, and metadata
        """
        query_lower = query.lower()
        
        # Step 1: Detect if this is a comprehensive/meta request
        is_comprehensive = cls._is_comprehensive_request(query_lower)
        is_health_check = cls._is_health_check(query_lower)
        is_analysis = cls._is_analysis_request(query_lower)
        
        # Step 2: Detect explicitly mentioned subsystems
        explicit_subsystems = cls._detect_explicit_subsystems(query_lower)
        
        # Step 3: Determine expansion strategy
        if is_comprehensive and (is_health_check or is_analysis):
            # Full expansion
            return cls._full_expansion(query, explicit_subsystems)
        elif explicit_subsystems:
            # Targeted expansion
            return cls._targeted_expansion(query, explicit_subsystems)
        elif is_health_check:
            # Default health check
            return cls._health_check_expansion(query)
        elif is_analysis:
            # Analysis without specific subsystem
            return cls._analysis_expansion(query, explicit_subsystems)
        else:
            # No expansion needed
            return cls._no_expansion(query)
    
    @classmethod
    def _is_comprehensive_request(cls, query: str) -> bool:
        """Check if query requests comprehensive/full analysis."""
        for pattern in cls.COMPREHENSIVE_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def _is_health_check(cls, query: str) -> bool:
        """Check if query is a health check request."""
        for pattern in cls.HEALTH_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def _is_analysis_request(cls, query: str) -> bool:
        """Check if query is an analysis request."""
        for pattern in cls.ANALYSIS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def _detect_explicit_subsystems(cls, query: str) -> List[str]:
        """Detect explicitly mentioned subsystems."""
        found = []
        for subsystem, config in cls.SUBSYSTEMS.items():
            for keyword in config["keywords"]:
                if re.search(keyword, query, re.IGNORECASE):
                    if subsystem not in found:
                        found.append(subsystem)
                    break
        return found
    
    @classmethod
    def _full_expansion(cls, query: str, 
                        explicit: List[str]) -> ExpandedIntent:
        """Expand to all subsystems for comprehensive request."""
        
        components = []
        
        # If explicit subsystems mentioned, prioritize them
        if explicit:
            for subsystem in explicit:
                components.extend(cls.SUBSYSTEMS[subsystem]["tools"])
        else:
            # All primary subsystems for health check
            for subsystem in ["cpu", "memory", "disk", "processes", "network"]:
                # Only primary tools (priority 1)
                for tool in cls.SUBSYSTEMS[subsystem]["tools"]:
                    if tool.priority == 1:
                        components.append(tool)
        
        return ExpandedIntent(
            original_query=query,
            detected_meta_intent="comprehensive_health_check",
            components=components,
            expansion_confidence=0.9 if explicit else 0.8,
            requires_all=True,
            estimated_complexity="complex",
            warnings=[] if explicit else [
                "⚠️ تم توسيع الطلب ليشمل جميع الأنظمة الفرعية الأساسية"
            ]
        )
    
    @classmethod
    def _targeted_expansion(cls, query: str,
                            subsystems: List[str]) -> ExpandedIntent:
        """Expand for specific mentioned subsystems."""
        
        components = []
        for subsystem in subsystems:
            components.extend(cls.SUBSYSTEMS[subsystem]["tools"])
        
        return ExpandedIntent(
            original_query=query,
            detected_meta_intent="targeted_analysis",
            components=components,
            expansion_confidence=0.95,
            requires_all=True,
            estimated_complexity="moderate" if len(subsystems) > 2 else "simple",
        )
    
    @classmethod
    def _health_check_expansion(cls, query: str) -> ExpandedIntent:
        """Default health check expansion."""
        
        components = []
        # Basic health: memory, disk, cpu
        for subsystem in ["memory", "disk", "cpu"]:
            for tool in cls.SUBSYSTEMS[subsystem]["tools"]:
                if tool.priority == 1:
                    components.append(tool)
        
        return ExpandedIntent(
            original_query=query,
            detected_meta_intent="basic_health_check",
            components=components,
            expansion_confidence=0.75,
            requires_all=True,
            estimated_complexity="simple",
            warnings=["ℹ️ فحص صحة أساسي — لفحص شامل استخدم: 'فحص صحة شامل'"]
        )
    
    @classmethod
    def _analysis_expansion(cls, query: str,
                            subsystems: List[str]) -> ExpandedIntent:
        """Analysis request without specific subsystem."""
        
        if subsystems:
            return cls._targeted_expansion(query, subsystems)
        
        # Default to memory if no subsystem specified
        return ExpandedIntent(
            original_query=query,
            detected_meta_intent="general_analysis",
            components=[cls.SUBSYSTEMS["memory"]["tools"][0]],
            expansion_confidence=0.6,
            requires_all=False,
            estimated_complexity="simple",
            warnings=["⚠️ لم يتم تحديد نظام فرعي — تم افتراض الذاكرة"]
        )
    
    @classmethod
    def _no_expansion(cls, query: str) -> ExpandedIntent:
        """No expansion needed — single intent."""
        return ExpandedIntent(
            original_query=query,
            detected_meta_intent=None,
            components=[],
            expansion_confidence=1.0,
            requires_all=False,
            estimated_complexity="simple",
        )
    
    # ==================== Utility Methods ====================
    
    @classmethod
    def get_tool_commands(cls, expanded: ExpandedIntent) -> List[Tuple[str, str]]:
        """Get list of (tool, command) tuples from expansion."""
        commands = []
        for comp in expanded.components:
            cmd = f"{comp.tool} {comp.args}".strip()
            commands.append((comp.subsystem, cmd))
        return commands
    
    @classmethod
    def summarize(cls, expanded: ExpandedIntent) -> Dict:
        """Summarize the expansion for logging/display."""
        return {
            "original_query": expanded.original_query,
            "meta_intent": expanded.detected_meta_intent,
            "subsystems": list(set(c.subsystem for c in expanded.components)),
            "tool_count": len(expanded.components),
            "confidence": expanded.expansion_confidence,
            "complexity": expanded.estimated_complexity,
            "warnings": expanded.warnings,
            "commands": cls.get_tool_commands(expanded),
        }


# ==================== Integration Helper ====================

def expand_intent(query: str) -> Dict:
    """
    Main entry point for intent expansion.
    
    Returns a dict suitable for ReAct loop integration.
    """
    expanded = MetaIntentExpander.expand(query)
    summary = MetaIntentExpander.summarize(expanded)
    
    return {
        "expanded": len(expanded.components) > 0,
        "original": query,
        "meta_intent": expanded.detected_meta_intent,
        "components": [
            {
                "subsystem": c.subsystem,
                "tool": c.tool,
                "args": c.args,
                "description": c.description,
                "optional": c.optional,
            }
            for c in expanded.components
        ],
        "confidence": expanded.expansion_confidence,
        "complexity": expanded.estimated_complexity,
        "requires_all": expanded.requires_all,
        "warnings": expanded.warnings,
        "suggested_plan": summary["commands"],
    }


# ==================== Self-Test ====================

if __name__ == "__main__":
    import json
    
    test_queries = [
        "كم استخدام الذاكرة؟",
        "حلّل CPU وRAM والقرص والعمليات الآن",
        "اعمل health check شامل",
        "فحص صحة شامل للنظام",
        "كم مساحة القرص المتبقية؟",
        "أعطني تقرير شامل عن حالة النظام",
        "what's the memory usage?",
        "full system diagnostic",
    ]
    
    print("🧠 Meta-Intent Expansion Test")
    print("=" * 60)
    
    for query in test_queries:
        result = expand_intent(query)
        print(f"\n📝 Query: {query}")
        print(f"   Meta-Intent: {result['meta_intent'] or 'None'}")
        print(f"   Components: {len(result['components'])}")
        print(f"   Confidence: {result['confidence']:.0%}")
        print(f"   Complexity: {result['complexity']}")
        if result['warnings']:
            print(f"   ⚠️ Warnings: {result['warnings']}")
        if result['suggested_plan']:
            print(f"   📋 Plan:")
            for subsystem, cmd in result['suggested_plan']:
                print(f"      [{subsystem}] {cmd}")
    
    print("\n" + "=" * 60)
    print("✅ Test Complete!")
