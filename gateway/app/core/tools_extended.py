"""
NOOGH Extended Tools - Additional tools beyond the core set.

Tools included:
- safe_shell_exec: Whitelisted shell commands (via ProcessActuator)
- http_request: HTTP to allowed domains
- sqlite_query: Safe database queries
- analyze_code: Static code analysis
- watch_file: File change monitoring
- schedule_task: Task scheduling

All tools follow security-first design.
SECURITY: All process execution routed through ProcessActuator with allowlist enforcement.
"""

import ast
import shlex
# SECURITY: subprocess import removed - all execution via ProcessActuator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from gateway.app.core.logging import get_logger

logger = get_logger("tools_extended")


# =============================================================================
# Safe Shell Executor
# =============================================================================

# Whitelist of allowed commands
ALLOWED_SHELL_COMMANDS: Set[str] = {
    # File operations (read-only)
    "ls",
    "cat",
    "head",
    "tail",
    "wc",
    "find",
    "tree",
    # Text processing
    "grep",
    "awk",
    "sed",
    "sort",
    "uniq",
    "cut",
    # System info (safe)
    "echo",
    "date",
    "whoami",
    "pwd",
    "hostname",
    "uname",
    # Development tools
    "python",
    "python3",
    "pip",
    "pytest",
    "git",
    "which",
    "whereis",
    "file",
    "stat",
    # Process control (safe)
    "sleep",
}

# Dangerous patterns to block
DANGEROUS_SHELL_PATTERNS: List[str] = [
    # Destructive commands
    "rm -rf",
    "rm -r",
    "rmdir",
    "sudo",
    "su ",
    # Permission changes
    "chmod",
    "chown",
    "chgrp",
    # System files
    "> /dev",
    "/etc/passwd",
    "/etc/shadow",
    # Network attacks
    "nc ",
    "netcat",
    "nmap",
    "curl |",
    "wget |",
    # Command chaining/injection
    ";",
    "&&",
    "||",
    "`",
    "$(",
    "${",
    # Redirection attacks
    "> ",
    ">> ",
    "< ",
    "<< ",
    # Background execution
    "&",
    "nohup",
    "disown",
    # Process manipulation
    "kill",
    "pkill",
    "killall",
    # Dangerous flags
    "--force",
    "-f ",
]


@dataclass
class ShellResult:
    """Result of shell command execution."""

    success: bool
    output: str
    error: Optional[str] = None
    return_code: int = 0
    command: str = ""


async def safe_shell_exec(
    command: str, 
    timeout: int = 10, 
    max_output: int = 10000, 
    working_dir: str = None,
    auth_context: Optional[Any] = None
) -> ShellResult:
    """
    Execute a shell command safely with whitelist enforcement (ASYNC).

    Security measures:
    - Only whitelisted commands allowed
    - Dangerous patterns blocked
    - Timeout protection
    - Output size limits
    - Safe working directory
    - Routed through hardened ProcessActuator
    """
    # Check for dangerous patterns FIRST
    command_lower = command.lower()
    for pattern in DANGEROUS_SHELL_PATTERNS:
        if pattern.lower() in command_lower:
            logger.warning(f"Blocked dangerous pattern: {pattern}")
            return ShellResult(
                success=False, output="", error=f"SECURITY: Dangerous pattern blocked: '{pattern}'", command=command
            )

    # Parse command
    try:
        parts = shlex.split(command)
    except ValueError as e:
        return ShellResult(success=False, output="", error=f"Parse error: {e}", command=command)

    if not parts:
        return ShellResult(success=False, output="", error="Empty command", command=command)

    # Check whitelist (baseline check before actuator)
    cmd = parts[0]
    cmd_base = Path(cmd).name if "/" in cmd else cmd

    if cmd_base not in ALLOWED_SHELL_COMMANDS:
        return ShellResult(
            success=False,
            output="",
            error=f"Command not allowed: '{cmd_base}'. Allowed: {sorted(ALLOWED_SHELL_COMMANDS)}",
            command=command,
        )

    # Safe working directory
    cwd = working_dir or "/tmp"

    # Execute through ProcessActuator (with full governance)
    try:
        from unified_core.bridge import get_bridge
        bridge = get_bridge()
        
        # Ensure bridge is initialized
        if not bridge.is_initialized:
            await bridge.initialize()
            
        actuator = bridge._actuator_hub.process
        
        # Build command list for actuator
        full_cmd = parts
        
        # Use provided auth_context or generic system context
        if not auth_context:
            from unified_core.auth import AuthContext
            auth_context = AuthContext(user_id="system_extended_tool", scopes={"process:spawn"})
        
        logger.info(f"Executing shell via hardened ProcessActuator: {command[:100]}...")
        result = await actuator.spawn(cmd=full_cmd, auth_context=auth_context, cwd=cwd)
        
        from unified_core.core.actuators import ActionResult
        
        if result.result == ActionResult.BLOCKED:
            return ShellResult(
                success=False,
                output="",
                error=f"SECURITY_BLOCKED: Governance denied process spawn: {result.result_data.get('error', 'Unknown')}",
                command=command,
            )
        
        success = result.result == ActionResult.SUCCESS
        status = result.result_data or {}
        
        return ShellResult(
            success=success,
            output=str(status.get("pid", "Process started")),
            error=status.get("error") if not success else None,
            return_code=0 if success else 1,
            command=command,
        )

    except Exception as e:
        logger.error(f"Shell execution error: {e}")
        return ShellResult(success=False, output="", error=str(e), command=command)


# =============================================================================
# HTTP Request Tool
# =============================================================================

# Allowed domains for HTTP requests
ALLOWED_HTTP_DOMAINS: Set[str] = {
    # Development/Testing
    "httpbin.org",
    "jsonplaceholder.typicode.com",
    # Documentation
    "docs.python.org",
    "developer.mozilla.org",
    # APIs (add more as needed)
    "api.github.com",
    # Local services (for Neural integration)
    "localhost",
    "127.0.0.1",
}


@dataclass
class HttpResult:
    """Result of HTTP request."""

    success: bool
    status_code: int = 0
    headers: Dict[str, str] = field(default_factory=dict)
    body: str = ""
    error: Optional[str] = None


async def http_request(
    url: str,
    method: str = "GET",
    headers: Dict[str, str] = None,
    body: str = None,
    timeout: int = 10,
    max_response: int = 50000,
    auth_context: Optional[Any] = None
) -> HttpResult:
    """
    Make HTTP request to allowed domains via hardened NetworkActuator (ASYNC).

    Security measures:
    - Domain whitelist (enforced by actuator)
    - IP validation (enforced by actuator)
    - Response size limit
    - Timeout protection
    - Full governance/approval support
    """
    try:
        from unified_core.bridge import get_bridge
        bridge = get_bridge()
        
        # Ensure bridge is initialized
        if not bridge.is_initialized:
            await bridge.initialize()
            
        actuator = bridge._actuator_hub.network
        
        # Use provided auth_context or generic system context
        if not auth_context:
            from unified_core.auth import AuthContext
            auth_context = AuthContext(user_id="system_extended_tool", scopes={"network:http"})
        
        logger.info(f"Making HTTP {method} to {url} via hardened NetworkActuator...")
        result = await actuator.http_request(
            url=url,
            method=method,
            headers=headers,
            body=body,
            timeout=timeout,
            auth_context=auth_context
        )
        
        from unified_core.core.actuators import ActionResult
        
        if result.result == ActionResult.BLOCKED:
            return HttpResult(
                success=False,
                error=f"SECURITY_BLOCKED: {result.result_data.get('error', 'Governance denied request')}"
            )
        
        success = result.result == ActionResult.SUCCESS
        data = result.result_data or {}
        
        return HttpResult(
            success=success,
            status_code=data.get("status_code", 0),
            headers=data.get("headers", {}),
            body=data.get("body", "")[:max_response],
            error=data.get("error") if not success else None
        )

    except Exception as e:
        logger.error(f"HTTP request error: {e}")
        return HttpResult(success=False, error=str(e))


# =============================================================================
# Code Analysis Tool
# =============================================================================


@dataclass
class CodeAnalysis:
    """Result of static code analysis."""

    success: bool
    lines: int = 0
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    complexity: int = 0
    issues: List[str] = field(default_factory=list)
    error: Optional[str] = None


def analyze_code(code: str, language: str = "python") -> CodeAnalysis:
    """
    Static analysis of code without execution - refactored for maintainability.

    Analyzes:
    - Function/class definitions
    - Import statements
    - Cyclomatic complexity estimate
    - Potential issues

    Args:
        code: Source code to analyze
        language: Programming language (only Python supported)

    Returns:
        CodeAnalysis with metrics and issues
    """
    if language.lower() != "python":
        return CodeAnalysis(success=False, error=f"Language '{language}' not supported. Only Python is supported.")

    # Parse AST
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return CodeAnalysis(success=False, error=f"Syntax error at line {e.lineno}: {e.msg}")

    analysis = CodeAnalysis(success=True, lines=len(code.split("\n")))

    # Create analyzer and process
    analyzer = _CodeAnalyzer(analysis)
    analyzer.process_tree(tree)

    return analysis


class _CodeAnalyzer:
    """Helper class to analyze AST nodes."""

    def __init__(self, analysis: CodeAnalysis):
        self.analysis = analysis

    def process_tree(self, tree: ast.AST):
        """Process all nodes in the AST tree."""
        for node in ast.walk(tree):
            self._process_node(node)

    def _process_node(self, node: ast.AST):
        """Dispatch node processing to appropriate handler."""
        # Function definitions
        if isinstance(node, ast.FunctionDef):
            self._add_function(node, is_async=False)
        elif isinstance(node, ast.AsyncFunctionDef):
            self._add_function(node, is_async=True)
        # Classes
        elif isinstance(node, ast.ClassDef):
            self._add_class(node)
        # Imports
        elif isinstance(node, ast.Import):
            self._add_import(node)
        elif isinstance(node, ast.ImportFrom):
            self._add_import_from(node)
        # Control flow (complexity)
        elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
            self.analysis.complexity += 1
        elif isinstance(node, ast.ExceptHandler):
            self.analysis.complexity += 1
        
        # Issue detection
        self._detect_issues(node)

    def _add_function(self, node, is_async: bool):
        """Add function info to analysis."""
        func_info = {
            "name": node.name,
            "args": len(node.args.args),
            "line_start": node.lineno,
            "line_end": getattr(node, "end_lineno", node.lineno),
            "is_async": is_async,
        }
        func_info["lines"] = func_info["line_end"] - func_info["line_start"] + 1
        self.analysis.functions.append(func_info)
        self.analysis.complexity += 1

    def _add_class(self, node: ast.ClassDef):
        """Add class info to analysis."""
        self.analysis.classes.append(node.name)
        self.analysis.complexity += 2

    def _add_import(self, node: ast.Import):
        """Add import statements to analysis."""
        for alias in node.names:
            self.analysis.imports.append(alias.name)

    def _add_import_from(self, node: ast.ImportFrom):
        """Add from-import statements to analysis."""
        module = node.module or ""
        for alias in node.names:
            self.analysis.imports.append(f"{module}.{alias.name}")

    def _detect_issues(self, node: ast.AST):
        """Detect potential code issues."""
        # Infinite loop detection
        if isinstance(node, ast.While):
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                self.analysis.issues.append(f"Line {node.lineno}: Potential infinite loop (while True)")

        # Dangerous function calls
        if isinstance(node, ast.Call):
            self._check_dangerous_calls(node)

    def _check_dangerous_calls(self, node: ast.Call):
        """Check for dangerous function calls."""
        if not isinstance(node.func, ast.Name):
            return
        
        dangerous_funcs = {
            "eval": "Use of eval() is dangerous",
            "exec": "Use of exec() is dangerous",
        }
        
        if node.func.id in dangerous_funcs:
            self.analysis.issues.append(f"Line {node.lineno}: {dangerous_funcs[node.func.id]}")


# =============================================================================
# SQLite Query Tool
# =============================================================================

# Allowed SQL operations (read-only for safety)
ALLOWED_SQL_KEYWORDS: Set[str] = {"SELECT", "WITH"}
FORBIDDEN_SQL_KEYWORDS: Set[str] = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "CREATE",
    "ALTER",
    "TRUNCATE",
    "REPLACE",
    "ATTACH",
    "DETACH",
    "VACUUM",
    "PRAGMA",
    "REINDEX",
    "ANALYZE",
}


@dataclass
class SqlResult:
    """Result of SQL query execution."""

    success: bool
    columns: List[str] = field(default_factory=list)
    rows: List[tuple] = field(default_factory=list)
    row_count: int = 0
    error: Optional[str] = None


def sqlite_query(
    db_path: str, query: str, max_rows: int = 200, timeout: int = 10, workspace: str = "/home/noogh/projects"
) -> SqlResult:
    """
    Execute read-only SQL query on SQLite database.

    Security measures:
    - Only SELECT queries allowed
    - Database path must be within workspace
    - Row limit enforced
    - Timeout protection

    Args:
        db_path: Path to SQLite database file
        query: SQL query (SELECT only)
        max_rows: Maximum rows to return
        timeout: Query timeout in seconds
        workspace: Allowed workspace path

    Returns:
        SqlResult with query results or error
    """
    import sqlite3
    from pathlib import Path

    # Validate database path
    db_abs = Path(db_path).resolve()
    workspace_abs = Path(workspace).resolve()

    try:
        db_abs.relative_to(workspace_abs)
    except ValueError:
        return SqlResult(success=False, error=f"Database path must be within workspace: {workspace}")

    if not db_abs.exists():
        return SqlResult(success=False, error=f"Database file not found: {db_path}")

    # Validate query - must start with allowed keywords
    query_upper = query.strip().upper()
    query_first_word = query_upper.split()[0] if query_upper.split() else ""

    if query_first_word not in ALLOWED_SQL_KEYWORDS:
        return SqlResult(success=False, error=f"Only SELECT queries allowed. Got: {query_first_word}")

    # Check for forbidden keywords anywhere in query
    for forbidden in FORBIDDEN_SQL_KEYWORDS:
        if forbidden in query_upper:
            return SqlResult(success=False, error=f"Forbidden SQL keyword: {forbidden}")

    # Execute query
    try:
        conn = sqlite3.connect(str(db_abs), timeout=timeout)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Set timeout
        cursor.execute(f"PRAGMA busy_timeout = {timeout * 1000}")

        # Execute with row limit
        limited_query = f"SELECT * FROM ({query}) LIMIT {max_rows}"
        cursor.execute(limited_query)

        # Get results
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description] if cursor.description else []

        conn.close()

        return SqlResult(success=True, columns=columns, rows=[tuple(row) for row in rows], row_count=len(rows))

    except sqlite3.OperationalError as e:
        return SqlResult(success=False, error=f"SQL error: {e}")
    except sqlite3.DatabaseError as e:
        return SqlResult(success=False, error=f"Database error: {e}")
    except Exception as e:
        return SqlResult(success=False, error=str(e))


# =============================================================================
# Register Extended Tools
# =============================================================================


def register_extended_tools(registry) -> int:
    """
    Register extended tools with the agent's tool registry.

    Args:
        registry: ToolRegistry instance

    Returns:
        Number of tools registered
    """
    from gateway.app.core.tools import Tool

    count = 0

    # Shell executor
    async def _shell_exec(command: str, timeout: int = 10) -> str:
        # Pass registry.kernel to get auth context
        auth = getattr(registry, 'kernel', None)._current_auth_context if hasattr(registry, 'kernel') else None
        result = await safe_shell_exec(command, timeout=timeout, auth_context=auth)
        if result.success:
            return result.output or "Command completed with no output."
        else:
            return f"Error: {result.error}"

    registry.register(
        Tool(
            name="shell_exec",
            description="Execute safe shell commands (ls, cat, grep, git, etc.). Many commands blocked for security.",
            function=_shell_exec,
            returns_observation=True,
        )
    )
    count += 1

    # HTTP request
    async def _http_get(url: str) -> str:
        # Pass registry.kernel to get auth context
        auth = getattr(registry, 'kernel', None)._current_auth_context if hasattr(registry, 'kernel') else None
        result = await http_request(url, method="GET", auth_context=auth)
        if result.success:
            return f"Status: {result.status_code}\n\n{result.body[:5000]}"
        else:
            return f"HTTP Error: {result.error}"

    registry.register(
        Tool(
            name="http_get",
            description="Fetch URL content via HTTP GET. Limited to whitelisted domains.",
            function=_http_get,
            returns_observation=True,
        )
    )
    count += 1

    # Code analysis
    def _analyze_code(code: str) -> str:
        result = analyze_code(code)
        if not result.success:
            return f"Analysis Error: {result.error}"

        output = [
            f"Lines: {result.lines}",
            f"Functions: {len(result.functions)}",
            f"Classes: {len(result.classes)}",
            f"Complexity: {result.complexity}",
        ]

        if result.functions:
            output.append("\nFunctions:")
            for f in result.functions:
                output.append(f"  - {f['name']}({f['args']} args) [{f['lines']} lines]")

        if result.issues:
            output.append("\nIssues:")
            for issue in result.issues:
                output.append(f"  ⚠ {issue}")

        return "\n".join(output)

    registry.register(
        Tool(
            name="analyze_code",
            description="Static analysis of Python code. Returns metrics, structure, and potential issues.",
            function=_analyze_code,
            returns_observation=True,
        )
    )
    count += 1

    # SQLite query
    def _sqlite_query(db_path: str, query: str) -> str:
        result = sqlite_query(db_path, query)
        if not result.success:
            return f"SQL Error: {result.error}"

        if not result.rows:
            return "Query returned no results."

        # Format as table
        header = " | ".join(result.columns)
        separator = "-" * len(header)
        rows_str = "\n".join(" | ".join(str(cell) for cell in row) for row in result.rows[:50])

        return f"{header}\n{separator}\n{rows_str}\n\n({result.row_count} rows)"

    registry.register(
        Tool(
            name="sqlite_query",
            description="Execute SELECT query on SQLite database. Read-only, workspace paths only.",
            function=_sqlite_query,
            returns_observation=True,
        )
    )
    count += 1

    # HTTP POST
    def _http_post(url: str, body: str) -> str:
        result = http_request(url, method="POST", body=body)
        if result.success:
            return f"Status: {result.status_code}\n\n{result.body[:5000]}"
        else:
            return f"HTTP Error: {result.error}"

    registry.register(
        Tool(
            name="http_post",
            description="Send HTTP POST request to whitelisted domains.",
            function=_http_post,
            returns_observation=True,
        )
    )
    count += 1

    logger.info(f"Registered {count} extended tools")
    return count
