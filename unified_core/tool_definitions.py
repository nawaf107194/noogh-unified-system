"""
Unified Tool Definitions for NOOGH System

This is the SINGLE SOURCE OF TRUTH for all tool definitions.
All layers (Gateway, Neural, Unified) must use these definitions.

Security: ALL tools with side-effects MUST route through actuators.
Pure functions (no side-effects) can execute directly.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class ToolCategory(Enum):
    """Tool categories for organization"""
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    PROCESS = "process"
    CODE = "code"
    MEMORY = "memory"
    SYSTEM = "system"
    DEVELOPMENT = "development"
    ML = "machine_learning"
    UTILITY = "utility"


class SecurityLevel(Enum):
    """Security risk levels"""
    SAFE = "safe"  # Pure functions, no side-effects
    LOW = "low"  # Read-only operations
    MEDIUM = "medium"  # Write operations with allowlists
    HIGH = "high"  # Process/network operations
    CRITICAL = "critical"  # Admin operations, requires explicit auth


@dataclass
class ToolDefinition:
    """
    Unified tool definition.
    
    Security Model:
    - Pure functions (actuator_type='pure') execute directly
    - Side-effects route through ActuatorHub with AMLA checks
    - Critical operations require explicit authorization
    """
    name: str
    description: str
    description_ar: str  # Arabic description
    category: ToolCategory
    security_level: SecurityLevel
    actuator_type: str  # 'pure', 'filesystem', 'network', 'process', 'sandbox'
    parameters: Dict[str, Dict[str, Any]]
    required: List[str] = field(default_factory=list)
    requires_amla: bool = False  # Force AMLA check even for reads
    requires_admin: bool = False  # Requires admin scope
    handler: Optional[Callable] = None  # Custom handler function
    
    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema format"""
        return {
            "name": self.name,
            "description": self.description,
            "description_ar": self.description_ar,
            "category": self.category.value,
            "security_level": self.security_level.value,
            "parameters": self.parameters,
            "required": self.required,
            "requires_amla": self.requires_amla,
            "requires_admin": self.requires_admin
        }


# =============================================================================
# CORE TOOL DEFINITIONS (Single Source of Truth)
# =============================================================================

UNIFIED_TOOLS: Dict[str, ToolDefinition] = {
    
    # =========================================================================
    # FILESYSTEM TOOLS
    # =========================================================================
    
    "fs.read": ToolDefinition(
        name="fs.read",
        description="Read content from a file",
        description_ar="قراءة محتوى ملف",
        category=ToolCategory.FILESYSTEM,
        security_level=SecurityLevel.LOW,
        actuator_type="filesystem",
        parameters={
            "path": {"type": "string", "description": "File path to read"}
        },
        required=["path"]
    ),
    
    "fs.write": ToolDefinition(
        name="fs.write",
        description="Write content to a file (creates directories if needed)",
        description_ar="كتابة محتوى إلى ملف",
        category=ToolCategory.FILESYSTEM,
        security_level=SecurityLevel.MEDIUM,
        actuator_type="filesystem",
        requires_amla=True,
        parameters={
            "path": {"type": "string", "description": "File path to write"},
            "content": {"type": "string", "description": "Content to write"}
        },
        required=["path", "content"]
    ),
    
    "fs.delete": ToolDefinition(
        name="fs.delete",
        description="Delete a file permanently (IRREVERSIBLE)",
        description_ar="حذف ملف نهائياً",
        category=ToolCategory.FILESYSTEM,
        security_level=SecurityLevel.HIGH,
        actuator_type="filesystem",
        requires_amla=True,
        requires_admin=True,
        parameters={
            "path": {"type": "string", "description": "File path to delete"}
        },
        required=["path"]
    ),
    
    "fs.list": ToolDefinition(
        name="fs.list",
        description="List files and directories",
        description_ar="عرض قائمة الملفات والمجلدات",
        category=ToolCategory.FILESYSTEM,
        security_level=SecurityLevel.SAFE,
        actuator_type="filesystem",
        parameters={
            "path": {"type": "string", "description": "Directory path to list"}
        },
        required=["path"]
    ),
    
    "fs.exists": ToolDefinition(
        name="fs.exists",
        description="Check if a file or directory exists",
        description_ar="التحقق من وجود ملف أو مجلد",
        category=ToolCategory.FILESYSTEM,
        security_level=SecurityLevel.SAFE,
        actuator_type="filesystem",
        parameters={
            "path": {"type": "string", "description": "Path to check"}
        },
        required=["path"]
    ),
    
    # =========================================================================
    # NETWORK TOOLS
    # =========================================================================
    
    "net.http_get": ToolDefinition(
        name="net.http_get",
        description="Send HTTP GET request",
        description_ar="إرسال طلب HTTP GET",
        category=ToolCategory.NETWORK,
        security_level=SecurityLevel.HIGH,
        actuator_type="network",
        requires_amla=True,
        parameters={
            "url": {"type": "string", "description": "URL to request"},
            "headers": {"type": "object", "description": "Optional headers"}
        },
        required=["url"]
    ),
    
    "net.http_post": ToolDefinition(
        name="net.http_post",
        description="Send HTTP POST request with data",
        description_ar="إرسال طلب HTTP POST مع بيانات",
        category=ToolCategory.NETWORK,
        security_level=SecurityLevel.HIGH,
        actuator_type="network",
        requires_amla=True,
        parameters={
            "url": {"type": "string", "description": "URL to request"},
            "data": {"type": "object", "description": "JSON data to send"},
            "headers": {"type": "object", "description": "Optional headers"}
        },
        required=["url"]
    ),
    
    # =========================================================================
    # PROCESS TOOLS
    # =========================================================================
    
    "proc.run": ToolDefinition(
        name="proc.run",
        description="Run a shell command (allowlist enforced)",
        description_ar="تنفيذ أمر shell (مع قائمة الأوامر المسموحة)",
        category=ToolCategory.PROCESS,
        security_level=SecurityLevel.CRITICAL,
        actuator_type="process",
        requires_amla=True,
        requires_admin=True,
        parameters={
            "command": {"type": "array", "description": "Command and arguments"},
            "cwd": {"type": "string", "description": "Working directory"}
        },
        required=["command"]
    ),
    
    # =========================================================================
    # CODE EXECUTION TOOLS
    # =========================================================================
    
    "code.exec_python": ToolDefinition(
        name="code.exec_python",
        description="Execute Python code in sandbox",
        description_ar="تنفيذ كود Python في بيئة معزولة",
        category=ToolCategory.CODE,
        security_level=SecurityLevel.CRITICAL,
        actuator_type="sandbox",
        requires_amla=True,
        parameters={
            "code": {"type": "string", "description": "Python code to execute"}
        },
        required=["code"]
    ),
    
    # =========================================================================
    # MEMORY TOOLS
    # =========================================================================
    
    "mem.search": ToolDefinition(
        name="mem.search",
        description="Search long-term semantic memory",
        description_ar="البحث في الذاكرة الدلالية طويلة المدى",
        category=ToolCategory.MEMORY,
        security_level=SecurityLevel.LOW,
        actuator_type="neural_client",
        parameters={
            "query": {"type": "string", "description": "Search query"},
            "n_results": {"type": "integer", "description": "Number of results", "default": 3}
        },
        required=["query"]
    ),
    
    "mem.record": ToolDefinition(
        name="mem.record",
        description="Record a new insight into long-term memory",
        description_ar="تسجيل معلومة جديدة في الذاكرة طويلة المدى",
        category=ToolCategory.MEMORY,
        security_level=SecurityLevel.MEDIUM,
        actuator_type="neural_client",
        parameters={
            "content": {"type": "string", "description": "Content to record"},
            "metadata": {"type": "object", "description": "Optional metadata"}
        },
        required=["content"]
    ),
    
    # =========================================================================
    # SYSTEM INFO TOOLS (Pure - psutil based)
    # =========================================================================
    
    "sys.info": ToolDefinition(
        name="sys.info",
        description="Get system information (CPU, RAM, Disk)",
        description_ar="الحصول على معلومات النظام (CPU، RAM، القرص)",
        category=ToolCategory.SYSTEM,
        security_level=SecurityLevel.SAFE,
        actuator_type="pure",
        parameters={}
    ),
    
    "sys.processes": ToolDefinition(
        name="sys.processes",
        description="List running processes (top 20 by memory)",
        description_ar="عرض العمليات الجارية (أعلى 20 بحسب الذاكرة)",
        category=ToolCategory.SYSTEM,
        security_level=SecurityLevel.LOW,
        actuator_type="pure",
        parameters={
            "limit": {"type": "integer", "description": "Max processes to return", "default": 20}
        }
    ),
    
    "sys.disk_usage": ToolDefinition(
        name="sys.disk_usage",
        description="Get disk usage for a directory",
        description_ar="الحصول على استخدام القرص لمجلد",
        category=ToolCategory.SYSTEM,
        security_level=SecurityLevel.SAFE,
        actuator_type="pure",
        parameters={
            "directory": {"type": "string", "description": "Directory path", "default": "/"}
        }
    ),
    
    "sys.gpu": ToolDefinition(
        name="sys.gpu",
        description="Get NVIDIA GPU status and VRAM usage",
        description_ar="الحصول على حالة معالج الرسوميات NVIDIA واستخدام الذاكرة (VRAM)",
        category=ToolCategory.SYSTEM,
        security_level=SecurityLevel.SAFE,
        actuator_type="pure",
        parameters={}
    ),
    
    "sys.execute": ToolDefinition(
        name="sys.execute",
        description="Execute a shell command (authorized only)",
        description_ar="تنفيذ أمر صدفة (للأوامر المصرح بها فقط)",
        category=ToolCategory.SYSTEM,
        security_level=SecurityLevel.HIGH,
        actuator_type="process",
        requires_amla=True,
        parameters={
            "command": {"type": "string", "description": "Shell command to run"}
        },
        required=["command"]
    ),
    
    # =========================================================================
    # DEVELOPMENT TOOLS (Skills-based)
    # =========================================================================
    
    "dev.repo_overview": ToolDefinition(
        name="dev.repo_overview",
        description="Analyze repository structure",
        description_ar="تحليل بنية المشروع",
        category=ToolCategory.DEVELOPMENT,
        security_level=SecurityLevel.SAFE,
        actuator_type="skills",
        parameters={
            "path": {"type": "string", "description": "Repository path", "default": "."}
        }
    ),
    
    "dev.search_code": ToolDefinition(
        name="dev.search_code",
        description="Search for code patterns",
        description_ar="البحث عن أنماط في الكود",
        category=ToolCategory.DEVELOPMENT,
        security_level=SecurityLevel.SAFE,
        actuator_type="skills",
        parameters={
            "pattern": {"type": "string", "description": "Search pattern"},
            "path": {"type": "string", "description": "Search path", "default": "."}
        },
        required=["pattern"]
    ),
    
    "dev.run_tests": ToolDefinition(
        name="dev.run_tests",
        description="Run test suite",
        description_ar="تشغيل الاختبارات",
        category=ToolCategory.DEVELOPMENT,
        security_level=SecurityLevel.MEDIUM,
        actuator_type="skills",
        parameters={
            "test_path": {"type": "string", "description": "Path to tests"}
        }
    ),
    
    "dev.git_status": ToolDefinition(
        name="dev.git_status",
        description="Get git repository status",
        description_ar="الحصول على حالة مستودع git",
        category=ToolCategory.DEVELOPMENT,
        security_level=SecurityLevel.SAFE,
        actuator_type="skills",
        parameters={}
    ),
    
    "dev.git_diff": ToolDefinition(
        name="dev.git_diff",
        description="Get git diff",
        description_ar="الحصول على الفروقات في git",
        category=ToolCategory.DEVELOPMENT,
        security_level=SecurityLevel.SAFE,
        actuator_type="skills",
        parameters={}
    ),
    
    "dev.find_entrypoints": ToolDefinition(
        name="dev.find_entrypoints",
        description="Find code entrypoints (main functions)",
        description_ar="إيجاد نقاط دخول الكود",
        category=ToolCategory.DEVELOPMENT,
        security_level=SecurityLevel.SAFE,
        actuator_type="skills",
        parameters={
            "path": {"type": "string", "description": "Search path", "default": "."}
        }
    ),
    
    # =========================================================================
    # MACHINE LEARNING TOOLS
    # =========================================================================
    
    "ml.load_dataset": ToolDefinition(
        name="ml.load_dataset",
        description="Load and analyze dataset from HuggingFace",
        description_ar="تحميل وتحليل مجموعة بيانات من HuggingFace",
        category=ToolCategory.ML,
        security_level=SecurityLevel.MEDIUM,
        actuator_type="ml_tools",
        parameters={
            "dataset_name": {"type": "string", "description": "HuggingFace dataset name"}
        },
        required=["dataset_name"]
    ),
    
    "ml.train_classifier": ToolDefinition(
        name="ml.train_classifier",
        description="Train a text classifier model",
        description_ar="تدريب نموذج تصنيف نصوص",
        category=ToolCategory.ML,
        security_level=SecurityLevel.HIGH,
        actuator_type="ml_tools",
        requires_amla=True,
        parameters={
            "dataset": {"type": "string", "description": "Dataset name"},
            "config": {"type": "object", "description": "Training configuration"}
        },
        required=["dataset"]
    ),
    
    "ml.search_datasets": ToolDefinition(
        name="ml.search_datasets",
        description="Search HuggingFace Hub for datasets",
        description_ar="البحث عن مجموعات بيانات في HuggingFace Hub",
        category=ToolCategory.ML,
        security_level=SecurityLevel.SAFE,
        actuator_type="ml_tools",
        parameters={
            "query": {"type": "string", "description": "Search query"}
        },
        required=["query"]
    ),
    
    "util.noop": ToolDefinition(
        name="util.noop",
        description="No operation (used when no action needed)",
        description_ar="لا عملية (تُستخدم عندما لا يوجد إجراء مطلوب)",
        category=ToolCategory.UTILITY,
        security_level=SecurityLevel.SAFE,
        actuator_type="pure",
        parameters={}
    ),
    
    "util.finish": ToolDefinition(
        name="util.finish",
        description="Signal task completion",
        description_ar="إشارة اكتمال المهمة",
        category=ToolCategory.UTILITY,
        security_level=SecurityLevel.SAFE,
        actuator_type="pure",
        parameters={
            "result": {"type": "string", "description": "Final result"}
        }
    ),
    "math.matrix_mult": ToolDefinition(
        name="math.matrix_mult",
        description="Perform optimized matrix multiplication (diagnostics)",
        description_ar="تنفيذ عملية ضرب مصفوفات محسنة (أغراض التشخيص)",
        category=ToolCategory.SYSTEM,
        security_level=SecurityLevel.MEDIUM,
        actuator_type="math",
        parameters={
            "size": {"type": "integer", "description": "Matrix size (N x N)", "default": 64}
        },
        required=["size"]
    ),
    
    # =========================================================================
    # AGENT ORCHESTRATION TOOLS
    # =========================================================================
    
    "agent.spawn": ToolDefinition(
        name="agent.spawn",
        description="Spawn a specialized autonomous agent (dev, secops, learning)",
        description_ar="استدعاء وكيل مستقل متخصص (تطوير، أمان، تعلم)",
        category=ToolCategory.DEVELOPMENT,
        security_level=SecurityLevel.HIGH,
        actuator_type="neural_client",
        parameters={
            "agent_type": {"type": "string", "description": "Type of agent: 'dev', 'secops', 'learning'"},
            "task": {"type": "string", "description": "Task for the agent"}
        },
        required=["agent_type", "task"]
    ),
    
    "agent.list": ToolDefinition(
        name="agent.list",
        description="List all available specialized agents",
        description_ar="استعراض كافة الوكلاء المتخصصين المتاحين",
        category=ToolCategory.DEVELOPMENT,
        security_level=SecurityLevel.SAFE,
        actuator_type="pure",
        parameters={}
    ),
    
    # =========================================================================
    # ADVANCED ANALYTICS TOOLS
    # =========================================================================
    
    "sys.analyze": ToolDefinition(
        name="sys.analyze",
        description="Deep intelligent analysis of system state and performance",
        description_ar="تحليل ذكي عميق لحالة النظام وأدائه",
        category=ToolCategory.SYSTEM,
        security_level=SecurityLevel.MEDIUM,
        actuator_type="neural_client",
        parameters={
            "query": {"type": "string", "description": "Subject to analyze"}
        },
        required=["query"]
    ),
    
    "sys.report": ToolDefinition(
        name="sys.report",
        description="Generate comprehensive system self-health report",
        description_ar="إنشاء تقرير فحص ذاتي شامل لحالة النظام",
        category=ToolCategory.SYSTEM,
        security_level=SecurityLevel.SAFE,
        actuator_type="pure",
        parameters={}
    ),
}


# Legacy name mappings for backward compatibility
LEGACY_NAME_MAP = {
    # Gateway legacy names → Unified names
    "exec_python": "code.exec_python",
    "read_file": "fs.read",
    "write_file": "fs.write",
    "list_files": "fs.list",
    "delete_file": "fs.delete",
    "system_shell": "proc.run",
    "read_system_file": "fs.read",  # DEPRECATED: was UNSAFE
    "write_system_file": "fs.write",  # DEPRECATED: was UNSAFE
    "get_system_info": "sys.info",
    "list_processes": "sys.processes",
    "search_memory": "mem.search",
    "record_insight": "mem.record",
    "remote_shell": "proc.run",  # Maps to safe proc.run with allowlist
    "repo_overview": "dev.repo_overview",
    "search_code": "dev.search_code",
    "run_tests": "dev.run_tests",
    "git_status": "dev.git_status",
    "git_diff": "dev.git_diff",
    "find_entrypoints": "dev.find_entrypoints",
    "load_dataset": "ml.load_dataset",
    "train_classifier": "ml.train_classifier",
    "search_datasets": "ml.search_datasets",
    
    # Neural/Unified legacy names
    "filesystem.read": "fs.read",
    "filesystem.write": "fs.write",
    "filesystem.delete": "fs.delete",
    "filesystem.list": "fs.list",
    "filesystem.exists": "fs.exists",
    "http.get": "net.http_get",
    "http.post": "net.http_post",
    "process.run": "proc.run",
    "calculator.compute": "util.noop",  # DEPRECATED: use direct Python
    "calculator.add": "util.noop",  # DEPRECATED
    "calculator.multiply": "util.noop",  # DEPRECATED
}


def get_tool_definition(name: str) -> Optional[ToolDefinition]:
    """Get tool definition by name (supports legacy names)"""
    # Try direct lookup
    if name in UNIFIED_TOOLS:
        return UNIFIED_TOOLS[name]
    
    # Try legacy mapping
    if name in LEGACY_NAME_MAP:
        unified_name = LEGACY_NAME_MAP[name]
        return UNIFIED_TOOLS.get(unified_name)
    
    return None


def get_tools_by_category(category: ToolCategory) -> List[ToolDefinition]:
    """Get all tools in a category"""
    return [tool for tool in UNIFIED_TOOLS.values() if tool.category == category]


def get_all_tool_schemas() -> List[Dict[str, Any]]:
    """Get all tool schemas in JSON format"""
    return [tool.to_schema() for tool in UNIFIED_TOOLS.values()]
