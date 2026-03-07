"""
Tool Executor for NOOGH
Handles tool extraction and execution from LLM responses.
Enhanced with PreambleManager and ProgressCheckpointManager.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple

# Neural Core Components
from neural_engine.preamble_manager import PreambleManager
from neural_engine.progress_checkpoint_manager import get_checkpoint_manager

# SECURITY: Safe math evaluation (P0 Fix - replaces eval())
from noogh.utils.security import safe_math_eval

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Executes tools called by ALLaM.
    
    Parses responses for tool calls like:
        [TOOL: get_system_status()]
        [TOOL: generate_image(prompt="قطة جميلة")]
    
    And executes them, returning results.
    """
    
    # Pattern to match tool calls
    TOOL_PATTERN = re.compile(
        r'\[TOOL:\s*(\w+)\s*\((.*?)\)\s*\]',
        re.DOTALL
    )
    
    # Tool Parallelization Configuration
    # Based on best practices from Qoder and Tasks System Prompt
    PARALLEL_TOOLS = {
        # Read-only operations - safe to run in parallel
        'read_file', 'list_directory', 'search_files',
        'get_system_status', 'get_time', 'check_agent_status',
        'search_memory', 'get_metrics'
    }
    
    SEQUENTIAL_TOOLS = {
        # Write/Execute operations - must run sequentially
        'write_file', 'edit_file', 'delete_file',
        'execute_command', 'run_terminal',
        'create_file', 'move_file',
        'update_memory', 'train_model'
    }
    
    def __init__(self, registry=None, max_tool_calls: int = 5):
        """
        Initialize executor.
        
        Args:
            registry: ToolRegistry instance
            max_tool_calls: Maximum tool calls per response
        """
        if registry is None:
            from .tool_adapter import get_tool_registry
            registry = get_tool_registry()
        
        self.registry = registry
        self.max_tool_calls = max_tool_calls
        
        # CRITICAL FIX: Initialize preamble_manager
        self.preamble_manager = PreambleManager()
        
        # FATAL-02 FIX: Initialize checkpoint_manager (was used at L340 but never set)
        self.checkpoint_manager = get_checkpoint_manager()
        
        logger.info(f"🔧 ToolExecutor initialized (max_calls={max_tool_calls})")
    
    def extract_tool_calls(self, response: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Extract tool calls from response text.
        
        Tries JSON format first (preferred), falls back to regex for legacy support.
        
        JSON Format:
            {"tool": "name", "args": {"key": "value"}}
        
        Legacy Format:
            [TOOL: get_system_status()]
            [TOOL: generate_image(prompt="قطة جميلة")]
        
        Args:
            response: Raw LLM response
            
        Returns:
            List of (tool_name, params) tuples
        """
        # Try JSON extraction first (preferred method)
        json_calls = self._extract_json_tool_calls(response)
        if json_calls:
            logger.info(f"🔧 Extracted {len(json_calls)} tool call(s) via JSON parser")
            # **FIX: Correct Arabic paths before returning**
            json_calls = [(name, self._fix_arabic_paths(params)) for name, params in json_calls]
            return json_calls[:self.max_tool_calls]
        
        # Try natural language format: "uses tool 'sys.execute': {...}"
        from neural_engine.tools.tool_call_parser import ToolCallParser
        natural_calls = ToolCallParser.parse_natural_call(response)
        if natural_calls:
            logger.info(f"🔧 Extracted {len(natural_calls)} tool call(s) via natural-language parser")
            natural_calls = [(name, self._fix_arabic_paths(params)) for name, params in natural_calls]
            return natural_calls[:self.max_tool_calls]
        
        # Fallback to legacy regex extraction
        regex_calls = self._extract_regex_tool_calls(response)
        if regex_calls:
            logger.warning(f"⚠️ Using legacy regex parser for {len(regex_calls)} tool call(s)")
            # **FIX: Correct Arabic paths before returning**
            regex_calls = [(name, self._fix_arabic_paths(params)) for name, params in regex_calls]
            regex_calls = [(name, self._fix_arabic_paths(params)) for name, params in regex_calls]
        return regex_calls[:self.max_tool_calls]
    
    def _fix_arabic_paths(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fix Arabic-translated paths in tool arguments.
        
        The Qwen model sometimes translates English paths like '/home/noogh' 
        into Arabic '/home/نووغ', causing command failures.
        
        This function reverts common translations back to English.
        """
        # Common translation map
        arabic_to_english = {
            'نووغ': 'noogh',
            'نووج': 'noogh',
            'مشروعات': 'projects',
            'مشاريع': 'projects',
            'البيانات': 'data',
            'الإعدادات': 'config',
            'المستخدمون': 'users',
        }
        
        def fix_string(text: str) -> str:
            if not isinstance(text, str):
                return text
            
            # Replace Arabic parts in paths
            for arabic, english in arabic_to_english.items():
                text = text.replace(arabic, english)
            
            return text
        
        # Recursively fix all string values in params
        fixed = {}
        for key, value in params.items():
            if isinstance(value, str):
                fixed[key] = fix_string(value)
            elif isinstance(value, dict):
                fixed[key] = self._fix_arabic_paths(value)
            elif isinstance(value, list):
                fixed[key] = [fix_string(v) if isinstance(v, str) else v for v in value]
            else:
                fixed[key] = value
        
        return fixed
    
    def _extract_json_tool_calls(self, response: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Extract tool calls from JSON format.
        
        Looks for: {"tool": "name", "args": {...}}
        Uses balanced brace matching to handle nested objects.
        """
        import json
        calls = []
        
        # Find all potential JSON tool call starting positions
        # Look for {"tool": pattern
        tool_marker = re.compile(r'\{\s*\"tool\"\s*:\s*\"([\w.]+)\"')
        
        for marker_match in tool_marker.finditer(response):
            start_idx = marker_match.start()
            
            # Extract balanced JSON object starting from this position
            json_str = self._extract_balanced_json(response, start_idx)
            if not json_str:
                continue
            
            try:
                obj = json.loads(json_str)
                if "tool" in obj:
                    tool_name = obj["tool"]
                    args = obj.get("args", {})
                    
                    # Validate tool name is alphanumeric/underscore only
                    if not re.match(r'^[\w.]+$', tool_name):
                        logger.warning(f"Invalid tool name format: {tool_name}")
                        continue
                    
                    # Validate args is a dict
                    if not isinstance(args, dict):
                        logger.warning(f"Tool args must be dict, got {type(args)}")
                        args = {}
                    
                    # SECURITY: Validate and sanitize arguments (FAIL-CLOSED)
                    try:
                        from .tool_validator import validate_tool_args, ValidationError
                        args = validate_tool_args(tool_name, args)
                    except ValidationError as e:
                        logger.error(
                            f"SECURITY: Tool argument validation failed for {tool_name}: {e}"
                        )
                        # Skip this tool call - do not execute unsafe args
                        continue
                    except ImportError as e:
                        # CRITICAL SECURITY: Validator MUST be available
                        # Running without validation = complete bypass of security controls
                        # This prevents: code injection, path traversal, SSRF, DoS
                        logger.critical(
                            "FATAL: Tool argument validator unavailable. "
                            "ToolExecutor CANNOT operate safely without input validation. "
                            "This is a security-critical failure."
                        )
                        raise ImportError(
                            "Tool argument validator (tool_validator.py) is REQUIRED. "
                            "Tool execution performs real actions and MUST validate inputs. "
                            f"Original error: {e}"
                        ) from e
                    
                    calls.append((tool_name, args))
                    logger.debug(f"Parsed JSON tool call: {tool_name}({args})")
                    
            except json.JSONDecodeError as e:
                logger.debug(f"JSON parse failed: {e}")
                continue
        
        return calls
    
    def _extract_balanced_json(self, text: str, start: int) -> Optional[str]:
        """
        Extract a balanced JSON object starting from the given position.
        Handles nested {} properly.
        """
        if start >= len(text) or text[start] != '{':
            return None
        
        depth = 0
        in_string = False
        escape_next = False
        
        for i in range(start, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if in_string:
                continue
            
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
        
        return None  # Unbalanced
    
    def _extract_regex_tool_calls(self, response: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Extract tool calls from legacy regex format: [TOOL: name(params)]
        
        Kept for backward compatibility.
        """
        calls = []
        
        for match in self.TOOL_PATTERN.finditer(response):
            tool_name = match.group(1)
            params_str = match.group(2).strip()
            
            # Parse parameters
            params = {}
            if params_str:
                # Try to parse as key=value pairs
                # Supports: prompt="text", n=5
                param_pattern = re.compile(r'(\w+)\s*=\s*(?:"([^"]*)"|(\d+)|(\w+))')
                for pm in param_pattern.finditer(params_str):
                    key = pm.group(1)
                    value = pm.group(2) or pm.group(3) or pm.group(4)
                    # Convert numeric strings
                    if pm.group(3):
                        value = int(value)
                    params[key] = value
            
            calls.append((tool_name, params))
        
        return calls
    
    async def execute_tool_calls(
        self, 
        response: str
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Execute all tool calls in a response.
        
        Args:
            response: LLM response containing tool calls
            
        Returns:
            Tuple of (has_calls, modified_response, results)
        """
        calls = self.extract_tool_calls(response)
        
        if not calls:
            return False, response, []
        
        results = []
        modified_response = response
        
        for tool_name, params in calls:
            # Generate preamble
            preamble = self.preamble_manager.create_preamble(tool_name, params)
            logger.info(preamble)
            
            result = await self.registry.execute(tool_name, params)
            results.append({
                "tool": tool_name,
                "params": params,
                "result": result
            })
            
            # Record for checkpoint
            success = result.get("success", False)
            summary = result.get("result", {}).get("summary_ar", str(result)[:100])
            checkpoint = self.checkpoint_manager.record_action(tool_name, success, summary)
            
            if checkpoint:
                report = self.checkpoint_manager.format_checkpoint_report(checkpoint)
                logger.info(report)
            
            # Replace tool call with result in response
            call_pattern = re.compile(
                rf'\[TOOL:\s*{re.escape(tool_name)}\s*\([^)]*\)\s*\]'
            )
            
            if result.get("success"):
                # Use Arabic summary if available
                summary = result.get("result", {}).get("summary_ar", str(result.get("result")))
                replacement = f"[نتيجة {tool_name}: {summary}]"
            else:
                replacement = f"[خطأ في {tool_name}: {result.get('error')}]"
            
            modified_response = call_pattern.sub(replacement, modified_response, count=1)
        
        return True, modified_response, results
    
    def has_tool_calls(self, response: str) -> bool:
        """Check if response contains tool calls."""
        return bool(self.TOOL_PATTERN.search(response))
    
    def get_tool_call_count(self, response: str) -> int:
        """Get number of tool calls in response."""
        return len(self.TOOL_PATTERN.findall(response))


# Initialize all tools
def initialize_all_tools():
    """Initialize and register all available tools.
    
    NOTE: The per-module register_*_tools() functions are now NO-OPs.
    All tool definitions live in unified_core.tools.definitions and
    are loaded by unified_core.tool_registry at startup.
    
    This function now only handles dataset-alias lambdas that cannot
    be expressed as static ToolDefinitions.
    """
    from .tool_adapter import get_tool_registry
    
    registry = get_tool_registry()
    
    # Legacy register calls — all NO-OPs now, kept for call-site compat
    from .system_tools import register_system_tools
    from .memory_tools import register_memory_tools
    from .media_tools import register_media_tools
    from .specialized_tools import register_specialized_tools
    from .agent_tools import register_agent_tools
    from .security_tools import register_security_tools
    
    register_system_tools(registry)
    register_memory_tools(registry)
    register_media_tools(registry)
    register_specialized_tools(registry)
    register_agent_tools(registry)
    register_security_tools(registry)
    
    # ===== DATASET TOOL ALIASES =====
    # Lambdas for model-hallucinated tool names — cannot be static defs
    from .system_tools import get_system_status, get_gpu_status, list_processes, get_current_time
    import os as _os
    
    # === SECURITY HELPERS (CVE-NE-01 fix) ===
    # Safe file operations — no shell, validated paths
    _ALLOWED_BASES = ("/home/noogh/", "/tmp/noogh_")
    
    def _validate_path(path: str) -> str:
        """Resolve and validate a file path against allowed base directories."""
        resolved = _os.path.realpath(_os.path.expanduser(path))
        if not any(resolved.startswith(base) for base in _ALLOWED_BASES):
            raise PermissionError(f"Path outside allowed directories: {resolved}")
        return resolved
    
    def _safe_read_file(path: str) -> dict:
        """Read a file using Python open() — no shell."""
        if not path:
            return {"success": False, "error": "path required"}
        try:
            safe_path = _validate_path(path)
            with open(safe_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return {"success": True, "result": content[:10000]}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _safe_write_file(path: str, content: str) -> dict:
        """Write a file using Python open() — no shell."""
        if not path or not content:
            return {"success": False, "error": "path and content required"}
        try:
            safe_path = _validate_path(path)
            _os.makedirs(_os.path.dirname(safe_path), exist_ok=True)
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "result": f"Written {len(content)} bytes to {safe_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _safe_list_dir(path: str = ".") -> dict:
        """List directory contents — no shell."""
        try:
            safe_path = _validate_path(path)
            entries = _os.listdir(safe_path)
            return {"success": True, "result": "\n".join(entries[:200])}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _safe_file_exists(path: str) -> dict:
        """Check if file exists — no shell."""
        if not path:
            return {"success": False, "error": "path required"}
        try:
            safe_path = _validate_path(path)
            return {"success": True, "result": "exists" if _os.path.exists(safe_path) else "not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _safe_search_code(query: str) -> dict:
        """Search Python files using subprocess with shell=False."""
        if not query:
            return {"success": False, "error": "query required"}
        try:
            import subprocess as _sp
            import shlex as _shlex
            result = _sp.run(
                ["grep", "-rn", query, "/home/noogh/projects/noogh_unified_system/src", "--include=*.py"],
                capture_output=True, text=True, timeout=15
            )
            lines = result.stdout.strip().split("\n")[:20]
            return {"success": True, "result": "\n".join(lines)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # FATAL-03 FIX: _get_learning_stats must be defined BEFORE DATASET_ALIASES
    def _get_learning_stats():
        try:
            from neural_engine.self_learner import get_learner
            learner = get_learner()
            return {"success": True, "result": learner.get_learning_stats()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    DATASET_ALIASES = {
        # System tools
        "sys.info": get_system_status,
        "sys.status": get_system_status,
        "sys.gpu": get_gpu_status,
        "sys.processes": list_processes,
        "sys.time": get_current_time,
        # File tools — SECURITY FIX (CVE-NE-01): Python-native, no shell
        "fs.read": lambda path="", **kw: _safe_read_file(path),
        "fs.write": lambda path="", content="", **kw: _safe_write_file(path, content),
        "fs.list": lambda path=".", **kw: _safe_list_dir(path),
        "fs.exists": lambda path="", **kw: _safe_file_exists(path),
        # fs.delete REMOVED — too dangerous via LLM
        # Network tools — REMOVED shell-based curl (CVE-NE-01)
        "net.http_get": lambda url="", **kw: {"success": False, "error": "HTTP tools disabled for security — use Python requests"},
        "net.http_post": lambda url="", data="", **kw: {"success": False, "error": "HTTP tools disabled for security — use Python requests"},
        # Dev tools — SECURITY FIX: shell=False grep
        "dev.search_code": lambda query="", **kw: _safe_search_code(query),
        "dev.repo_overview": lambda **kw: {"success": True, "result": str(len([f for r, d, fs in _os.walk("/home/noogh/projects/noogh_unified_system/src") for f in fs if f.endswith('.py')])) + " Python files"},
        # Utility
        "util.noop": lambda **kw: {"success": True, "result": "No operation performed"},
        # Stock/Market analysis (placeholder)
        "StockAnalysis": lambda **kw: {"success": True, "result": "تحليل السوق غير متاح حالياً - استخدم أدوات أخرى"},
        "debug": lambda **kw: get_system_status(),
        "educational_guidance": lambda **kw: {"success": True, "result": "استخدم الموارد التعليمية المتاحة"},
        # Math tools - SECURITY FIX: Use safe_math_eval instead of eval()
        "simple_math": lambda expression="", **kw: {"success": True, "result": str(safe_math_eval(expression)) if expression else "expression required"},
        "math.calculate": lambda expression="", **kw: {"success": True, "result": str(safe_math_eval(expression)) if expression else "expression required"},
        # Meta tools
        "tool_call": lambda **kw: {"success": True, "result": "استخدم الأدوات المتاحة"},
        "ToolCall": lambda **kw: {"success": True, "result": "استخدم الأدوات المتاحة"},
        # Model hallucinated tools - map to real functionality
        "SystemAnalyzer": lambda **kw: get_system_status(),
        "system_analyzer": lambda **kw: get_system_status(),
        "questioner": lambda query="", **kw: {"success": True, "result": f"استفسار: {query}"},
        # Search — SECURITY FIX: shell=False grep
        "search": lambda query="", **kw: _safe_search_code(query),
        "code_search": lambda query="", **kw: _safe_search_code(query),
        "analyzer": lambda **kw: get_system_status(),
        "monitor": lambda **kw: get_gpu_status(),
        "info": lambda **kw: get_system_status(),
        "status": lambda **kw: get_system_status(),
        # Creative/thinking tools - return success so model continues with answer
        "Brainstorming": lambda topic="", **kw: {"success": True, "result": f"أفكار حول: {topic}" if topic else "فكرة إبداعية"},
        "brainstorming": lambda topic="", **kw: {"success": True, "result": f"أفكار حول: {topic}" if topic else "فكرة إبداعية"},
        "creative_writing": lambda theme="", **kw: {"success": True, "result": f"كتابة إبداعية عن: {theme}" if theme else "إبداع"},
        "thinking": lambda **kw: {"success": True, "result": "تفكير..."},
        "reasoning": lambda **kw: {"success": True, "result": "استنتاج..."},
        "searcher": lambda **kw: {"success": True, "result": "بحث..."},
        "web_search": lambda **kw: {"success": True, "result": "بحث ويب غير متاح حالياً"},
        # Additional hallucinated tools
        "MemoryLearner": lambda **kw: {"success": True, "result": "التعلم من الذاكرة..."},
        "reflect": lambda **kw: {"success": True, "result": "تأمل وتفكير..."},
        "ToolExecution": lambda **kw: {"success": True, "result": "تنفيذ..."},
        "tool_execution": lambda **kw: {"success": True, "result": "تنفيذ..."},
        "Philosophy": lambda **kw: {"success": True, "result": "فلسفة الحياة هي التعلم والنمو المستمر"},
        "Wisdom": lambda prompt="", **kw: {"success": True, "result": "الحكمة تأتي من التجربة والتأمل"},
        "wisdom": lambda **kw: {"success": True, "result": "الحكمة تأتي من التجربة والتأمل"},
        "generate": lambda **kw: {"success": True, "result": "توليد..."},
        "create": lambda **kw: {"success": True, "result": "إنشاء..."},
        # Shell aliases REMOVED — direct shell execution too dangerous (CVE-NE-01)
        # "shell_exec", "exec", "run" — REMOVED
        # Poetry/writing
        "poetry": lambda **kw: {"success": True, "result": "شعر..."},
        "write_poem": lambda **kw: {"success": True, "result": "كتابة شعر..."},
        "storytelling": lambda **kw: {"success": True, "result": "سرد القصة..."},
        # Learning system tools
        "learning_stats": lambda **kw: _get_learning_stats(),
        "get_learning_stats": lambda **kw: _get_learning_stats(),
    }
    
    # _get_learning_stats moved above DATASET_ALIASES (FATAL-03 fix)
    
    # Register dataset aliases via the adapter (which wraps unified_core)
    for alias_name, func in DATASET_ALIASES.items():
        try:
            registry.register_function(alias_name, func)
        except (AttributeError, TypeError):
            # Adapter may not support register_function; skip gracefully
            logger.debug(f"Skipping dataset alias {alias_name} — adapter does not support register_function")
    
    logger.info(f"✅ All tools initialized (dataset aliases: {len(DATASET_ALIASES)})")
    return registry


# Global executor instance
_executor: Optional[ToolExecutor] = None

def get_tool_executor() -> ToolExecutor:
    """Get or create global tool executor."""
    global _executor
    if _executor is None:
        # Initialize tools first
        initialize_all_tools()
        _executor = ToolExecutor()
    return _executor
