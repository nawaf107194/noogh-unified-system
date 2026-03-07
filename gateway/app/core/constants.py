"""
Constants for NOOGH Gateway System.
Centralized location for all magic numbers and hard-coded strings.
"""


# ============================================================================
# LLM Generation Parameters
# ============================================================================
class LLMConfig:
    """LLM generation configuration"""

    MAX_NEW_TOKENS = 512
    MAX_NEW_TOKENS_RETRY = 512
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_TOP_P = 0.95


# ============================================================================
# Agent Kernel Configuration
# ============================================================================
class AgentConfig:
    """Agent kernel configuration"""

    # Iteration limits
    MAX_ITERATIONS = 5
    MAX_PROTOCOL_RETRIES = 2

    # Context window
    MAX_CONTEXT_LENGTH = 2000
    MAX_CONTEXT_ENTRY_LENGTH = 500
    MAX_RECENT_EXCHANGES = 6

    # Answer limits
    MAX_FINAL_ANSWER_LENGTH = 10000
    MAX_INTERMEDIATE_ANSWER_LENGTH = 5000
    ANSWER_TRUNCATION_SUFFIX = "\n\n...[Output truncated to {length} characters]"


# ============================================================================
# Budget Limits
# ============================================================================
class BudgetLimits:
    """Resource budget limits"""

    # Time budgets (milliseconds)
    MAX_TOTAL_TIME_MS = 30000  # 30 seconds
    MAX_EXEC_TIME_MS = 10000  # 10 seconds total for code execution

    # File operation budgets
    MAX_BYTES_READ = 5 * 1024 * 1024  # 5MB
    MAX_WRITE_BYTES = 1 * 1024 * 1024  # 1MB
    MAX_FILES_READ = 10

    # Step budget
    DEFAULT_MAX_STEPS = 5


# ============================================================================
# Redis Configuration
# ============================================================================
class RedisConfig:
    """Redis keys and TTL configuration"""

    # Keys
    KEY_WORKER_HEARTBEAT = "noogh:worker:heartbeat"
    KEY_JOBS_QUEUE = "jobs:queue"
    KEY_JOBS_DATA_PREFIX = "jobs:data:"

    # TTL (seconds)
    HEARTBEAT_TTL = 30
    HEARTBEAT_INTERVAL = 5
    HEARTBEAT_MAX_AGE = 15  # For readiness check

    # Timeouts
    QUEUE_BLOCK_TIMEOUT = 2


# ============================================================================
# Error Prefixes
# ============================================================================
class ErrorPrefixes:
    """Standard error message prefixes"""

    UNSUPPORTED = "UNSUPPORTED:"
    EXECUTION_ERROR = "EXECUTION_ERROR:"
    UNAUTHORIZED = "UNAUTHORIZED:"
    PROTOCOL_ERROR = "ERROR: Protocol violation"


# ============================================================================
# Error Types
# ============================================================================
class ErrorTypes:
    """Standard error type identifiers"""

    UNSUPPORTED = "UNSUPPORTED"
    BUDGET = "BUDGET"
    TIMEOUT = "TIMEOUT"
    PROTOCOL_VIOLATION = "PROTOCOL_VIOLATION"
    PROTOCOL_FALLBACK = "PROTOCOL_FALLBACK"
    INSUFFICIENT_SCOPE = "INSUFFICIENT_SCOPE"
    EXEC_DISABLED = "EXEC_DISABLED"
    EXECUTION_BLOCKED = "EXECUTION_BLOCKED_IN_PLAN_MODE"
    PARSE_ERROR = "ParseError"
    BUDGET_EXCEEDED = "BudgetExceeded"
    TOTAL_TIME_BUDGET_EXCEEDED = "TOTAL_TIME_BUDGET_EXCEEDED"
    EXECUTION_BUDGET_EXCEEDED = "EXECUTION_BUDGET_EXCEEDED"
    FILE_READ_BUDGET_EXCEEDED = "FILE_READ_BUDGET_EXCEEDED"
    WRITE_BUDGET_EXCEEDED = "WRITE_BUDGET_EXCEEDED"


# ============================================================================
# Worker Configuration
# ============================================================================
class WorkerConfig:
    """Background worker configuration"""

    HEARTBEAT_WRITE_INTERVAL = 5  # seconds
    JOB_POLL_TIMEOUT = 2  # seconds
    MAX_RETRY_ATTEMPTS = 3
    PLAN_RETRY_DELAY = 1  # seconds


# ============================================================================
# API Configuration
# ============================================================================
class APIConfig:
    """API and middleware configuration"""

    # Rate limiting
    DEFAULT_REQUESTS_PER_MINUTE = 60
    INTERNAL_REQUESTS_PER_MINUTE = 200

    # Request limits
    MAX_REQUEST_SIZE_BYTES = 1024 * 1024  # 1MB
    INTERNAL_MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB

    # Task limits
    MAX_TASK_LENGTH = 10000
    MIN_TASK_LENGTH = 1


# ============================================================================
# Protocol Messages
# ============================================================================
class ProtocolMessages:
    """Standard protocol-related messages"""

    NO_BRAIN = f"{ErrorPrefixes.UNSUPPORTED} Brain not initialized"
    BUDGET_EXCEEDED = f"{ErrorPrefixes.UNSUPPORTED} Total task time budget exceeded"
    MAX_ITERATIONS = f"{ErrorPrefixes.UNSUPPORTED} Maximum iterations reached without solution"
    EXEC_DISABLED = f"{ErrorPrefixes.UNSUPPORTED} Execution disabled by configuration"
    TOOL_BLOCKED_PLAN_MODE = f"{ErrorPrefixes.UNSUPPORTED} Tool execution blocked in Planning Mode"
    EXEC_TIME_BUDGET = f"{ErrorPrefixes.UNSUPPORTED} Execution time budget exceeded"
    FILE_READ_LIMIT = f"{ErrorPrefixes.UNSUPPORTED} File read limit exceeded"
    WRITE_LIMIT = f"{ErrorPrefixes.UNSUPPORTED} Write budget exceeded"
    PROTOCOL_RETRIES_EXCEEDED = f"{ErrorPrefixes.UNSUPPORTED} Protocol violation persists after {{retries}} retries"


# ============================================================================
# Sanitization Patterns
# ============================================================================
class SanitizationPatterns:
    """Regex patterns for answer sanitization"""

    # Internal artifacts
    RECENT_CONTEXT = r"Recent Context:.*?(?=THINK:|$)"
    TASK_PREFIX = r"Task:.*?(?=THINK:|Recent Context:|$)"
    USER_PREFIX = r"USER:.*?(?=AGENT:|THINK:|$)"
    AGENT_PREFIX = r"AGENT:.*?(?=USER:|THINK:|$)"
    INTENT_CAPABILITY = r"INTENT:.*?CAPABILITY:[^\n]+"
    CODE_BLOCK_REMOVED = r"\[CODE BLOCK REMOVED\]"
    INLINE_CODE_REMOVED = r"\[INLINE CODE REMOVED\]"
    REMOVED_MARKER = r"\[REMOVED\]"

    # Protocol feedback
    ACTUAL_FORMAT = r"Actual format:.*?try again\.?"
    REVIEW_FORMAT = r"Please review the format rules.*"
    FOLLOW_FORMAT = r"Please follow the format exactly.*"
    THINK_ACT_REFLECT = r"THINK\s*->\s*ACT\s*->\s*REFLECT\s*->\s*ANSWER"
    ERROR_PROTOCOL = r"ERROR: Protocol violation.*"
    SYSTEM_INSTRUCTION = r"\[SYSTEM INSTRUCTION:.*?\]"
    PLANNING_MODE = r"PLANNING MODE ACTIVE.*"
    DO_NOT_EXECUTE = r"DO NOT EXECUTE CODE.*"
    EXECUTION_ALLOWED = r"execution_allowed=\w+\)"

    # Policy debug
    POLICY_DEBUG = r"===\s*POLICY DEBUG\s*===.*?===\s*END POLICY DEBUG"

    # Sections
    EQUALS_SECTIONS = r"={3,}.*?={3,}"

    # Code blocks (for final answers)
    CODE_BLOCK = r"```.*?```"
    INLINE_CODE = r"`[^`]+`"

    # Dangerous patterns
    IMPORT_OS = r"import\s+os\s*$"
    IMPORT_SUBPROCESS = r"import\s+subprocess\s*$"
    EVAL_FUNC = r"eval\s*\("
    EXEC_FUNC = r"exec\s*\("
    IMPORT_FUNC = r"__import__\s*\("
    OPEN_FUNC = r"open\s*\([^)]*\)"
    SUBPROCESS_RUN = r"subprocess\.run"
    OS_SYSTEM = r"os\.system"


# ============================================================================
# Tool Scopes
# ============================================================================
class ToolScopes:
    """Required scopes for each tool"""

    EXEC_PYTHON = {"exec"}
    READ_FILE = {"fs:read"}
    WRITE_FILE = {"fs:write"}
    LIST_FILES = {"fs:read"}
    SEARCH_CODE = {"tools:use"}
    RUN_TESTS = {"tools:use"}
    GIT_STATUS = {"tools:use"}
    GIT_DIFF = {"tools:use"}
    NONE = set()

    # Mapping
    TOOL_SCOPE_MAP = {
        "exec_python": EXEC_PYTHON,
        "read_file": READ_FILE,
        "write_file": WRITE_FILE,
        "list_files": LIST_FILES,
        "search_code": SEARCH_CODE,
        "run_tests": RUN_TESTS,
        "git_status": GIT_STATUS,
        "git_diff": GIT_DIFF,
        "none": NONE,
    }


# ============================================================================
# File Paths
# ============================================================================
class FilePaths:
    """Standard file paths"""

    SYSTEM_PROMPT_FILE = "prompts/agent_system_prompt.txt"
    PLAN_FILE_TEMPLATE = "PLAN_{plan_id}.json"
